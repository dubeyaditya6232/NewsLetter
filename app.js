import dotenv from "dotenv";
dotenv.config();
import natural from 'natural';
import fs from "fs";
import { sendEmail } from "./mail/mail.js";
import { fetchFromGNews, fetchFromNewsAPI } from "./articles.js";


const maxRetries = 3;

const doYouKnow = async (keyword) => {
    const prompt = `You are an expert AI assistant that generates a "Did You Know?" section for a newsletter about generative AI.
    Generate a fun fact or interesting information about "${keyword}" in the context of generative AI. 1-2 sentences only.
    Do not include any explanations or headers.`;
    const requestPayload = {
        contents: [{ role: 'user', parts: [{ text: prompt }] }]
    };
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    const response = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=' + process.env.GOOGLE_API_KEY, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestPayload),
        signal: controller.signal
    });
    clearTimeout(timeout);
    const data = await response.json();
    const content = data?.candidates?.[0]?.content?.parts?.[0]?.text;
    return content

}

async function rankArticlesWithLLM(articles) {
    const prompt = `You are an expert AI assistant that filters and ranks news articles about generative AI.
    Only retain articles that highlight genuine technological advancements or research.
    Return ONLY a valid JSON array sorted by importance with keys: title, summary, url. Do not include any explanations or headers. 
    Rank the most important articles first.Remove articles which have less than 20 words in the summary.
    Here are the articles:
  ${articles.map((a, i) => `${i + 1}. Title: ${a.title}\nURL: ${a.url}`).join('\n\n')}
  Return the top articles in a JSON array sorted by importance with keys: title, summary, url.`;
    const requestPayload = {
        contents: [{ role: 'user', parts: [{ text: prompt }] }]
    };

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 15000);

            const response = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=' + process.env.GOOGLE_API_KEY, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestPayload),
                signal: controller.signal
            });
            clearTimeout(timeout);

            const data = await response.json();
            const content = data?.candidates?.[0]?.content?.parts?.[0]?.text;

            if (!content) throw new Error('Gemini returned no content');
            const jsonMatch = content.match(/\[.*\]/s);
            if (!jsonMatch) throw new Error('No valid JSON array found in Gemini response');

            const parsed = JSON.parse(jsonMatch[0]);
            return parsed.slice(0, 50);
        }
        catch (err) {
            console.error(`Attempt ${attempt} failed:`, err.message);
            if (attempt === maxRetries) {
                console.warn('Max retries reached. Falling back to original article list.');
                return articles.slice(0, 50);
            }
            await new Promise(res => setTimeout(res, 1000 * attempt));
        }
    }
}

function populateTemplate(template, articles) {
    const articleHtml = articles.map((a, i) => `
    <div style="margin-bottom: 25px; padding: 7px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
      <h3 style="color: #2c3e50;"><a href="${a.url}" target="_blank" style="text-decoration: none; color: #2980b9;">${a.title}</a></h3>
      <p style="font-size: 16px; line-height: 1.5; color: #555;">${a.summary}</p>
    </div>
  `).join('');

    return template.replace('{{articles}}', articleHtml);
}

const fetchNews = async () => {
    const [newsApiArticles, gnewsArticles] = await Promise.all([
        fetchFromNewsAPI(),
        // fetchFromGNews()
    ]);
    // const allArticles = [...newsApiArticles, ...gnewsArticles];
    // const uniqueArticles = Array.from(new Map(allArticles.map(a => [a.url, a])).values());
    // uniqueArticles.filter(a => a.summary !== 'No summary available.');
    // const rankedArticles = await rankArticlesWithLLM(uniqueArticles);
    const rankedArticles = await rankArticlesWithLLM(newsApiArticles);
    console.log('Ranked articles:', rankedArticles[0]);
    return rankedArticles;
}

const { WordTokenizer, PorterStemmer, TfIdf } = natural;

const extractKeywords=(articles)=> {
    // Initialize NLP tools
    const tokenizer = new WordTokenizer();
    const tfidf = new TfIdf();

    // Expanded stopwords list
    const stopwords = new Set([
        'the', 'a', 'ai', 'an', 'of', 'in', 'and', 'to', 'for', 'with',
        'on', 'by', 'at', 'from', 'as', 'is', 'are', 'was', 'be', 'this',
        'that', 'it', 'will', 'can', 'has', 'have', 'but', 'or', 'not',
        'new', 'announces', 'says', 'using', 'based', 'today', 'announces',
        'latest', 'platform', 'technology', 'solution'
    ].map(word => word.toLowerCase()));

    // Process each article
    articles.forEach(article => {
        // Combine title and summary for better context
        const text = `${article.title} ${article.summary || ''}`;
        tfidf.addDocument(text);
    });

    // Extract keywords from all documents
    const keywords = new Map();

    articles.forEach((article, docIndex) => {
        const text = `${article.title} ${article.summary || ''}`;
        const terms = tokenizer.tokenize(text);

        // Get unique terms with their TF-IDF scores
        const scores = new Map();
        terms.forEach(term => {
            term = term.toLowerCase();
            // Filter conditions
            if (term.length < 3) return; // Skip short terms
            if (stopwords.has(term)) return; // Skip stopwords
            if (!/^[a-z]/i.test(term)) return; // Must start with letter
            if (/\d/.test(term)) return; // Skip terms with numbers

            const score = tfidf.tfidf(term, docIndex);
            scores.set(term, (scores.get(term) || 0) + score);
        });

        // Accumulate scores across all documents
        scores.forEach((score, term) => {
            keywords.set(term, (keywords.get(term) || 0) + score);
        });
    });

    // Sort and return top keywords
    return Array.from(keywords)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([term]) => term.charAt(0).toUpperCase() + term.slice(1));
}

function extractKeywords1(articles) {
    // Simple keyword extraction: count frequencies of capitalized words (excluding stopwords)
    const stopwords = new Set(['The', 'A', 'AI', 'An', 'Of', 'In', 'And', 'To', 'For', 'With', 'On', 'By', 'At', 'From', 'As', 'Is', 'Are', 'Was', 'Be', 'This', 'That', 'It', 'Will', 'Can', 'Has', 'Have', 'But', 'Or', 'Not']);
    const freq = {};
    articles.forEach(a => {
        const words = a.title.match(/\b[A-Z][a-zA-Z0-9\-]+\b/g) || [];
        words.forEach(w => {
            if (!stopwords.has(w)) freq[w] = (freq[w] || 0) + 1;
        });
    });
    // Return top 1-2 keywords
    // Sort by frequency and return the top 2 keywords
    return Object.entries(freq)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 2)
        .map(x => x[0]);
}

const getCurrentMonthAndYear = () => {
    const date = new Date();
    const options = { month: 'long', year: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

const generateHtmlTemplate = (articles, mainKeyword, generatePoints) => {
    let html = `
<div class="container">
    <h1>GenAI Weekly Digest</h1>
    <p><em>Happenings in Generative AI: ${getCurrentMonthAndYear()}</em></p>
    <div class="digest-flex">
        <!-- Left Column: 30% -->
        <div class="side-section">
            <div class="did-you-know">
                <h2>💡 Did You Know?</h2>
                <strong>${mainKeyword}</strong> is a trending topic in GenAI this week. Stay tuned for more insights!
                <p>${generatePoints}</p>
            </div>
            <div class="whats-next">
                <h2>🔮 What's Next?</h2>
                Watch for further developments in <strong>${mainKeyword}</strong> as the GenAI landscape evolves. Next week may bring more breakthroughs!
            </div>
        </div>
        <!-- Right Column: 70% -->
        <div class="main-section">
            <h2>📰 This Week's Top GenAI News</h2>
            <ul class="news-list">`;

    articles.forEach(article => {
        html += `
        <li>
            <strong>${article.title}</strong><br/>
            <small>${article.summary}</small>
        </li>`;
    });

    html += `
            </ul>
        </div>
    </div>
    <footer style="margin-top: 40px; color: #888; font-size: 0.95em;">
        &middot; Powered by the latest GenAI news
    </footer>
</div>
<style>
body { font-family: 'Segoe UI', Arial, sans-serif; background: #eaf6fb; margin: 0; color: #222; }
.container { max-width: 1000px; margin: 32px auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.07); padding: 32px; }
h1 { color: #2b6cb0; margin-top: 0; }
h2 { color: #234e70; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-top: 0; }
.digest-flex {
    display: flex;
    gap: 32px;
}
.side-section {
    flex: 0 0 30%;
    display: flex;
    flex-direction: column;
    gap: 24px;
}
.did-you-know, .whats-next {
    background: #f0f4f8;
    border-left: 4px solid #2b6cb0;
    padding: 16px 20px;
    border-radius: 8px;
}
.main-section {
    flex: 1 1 70%;
}
.news-list { list-style: none; padding: 0; }
.news-list li { margin-bottom: 20px; }
.keyword { display: inline-block; background: #e2eafc; color: #234e70; padding: 2px 10px; border-radius: 8px; font-weight: bold; margin-left: 8px; }
@media (max-width: 900px) {
    .digest-flex { flex-direction: column; }
    .side-section, .main-section { flex: 1 1 100%; }
}
@media (max-width: 600px) {
    .container { padding: 14px; }
}
</style>
`;
    return html;
}

let articles = await fetchNews()
console.log('Fetched articles:', articles.length);
const template = fs.readFileSync('./mail/newsletter_template.html', 'utf-8');
if (articles.length === 0) {
    console.log('No articles found. Exiting...');
} else {
    // const html = populateTemplate(template, articles);
    // sendEmail(html, process.env.RECIPIENT_EMAIL)

    const keywords = extractKeywords(articles);
    console.log('Extracted keywords:', keywords);
    const mainKeyword = keywords[0] || 'GenAI';
    const mainKeyword2 = keywords[1];
    console.log('Main keyword:', mainKeyword);
    const generatePoints = await doYouKnow(mainKeyword, mainKeyword2);
    console.log('Did you know:', generatePoints);
    const html = generateHtmlTemplate(articles, mainKeyword, generatePoints);
    fs.writeFileSync('./mail/newsletter.html', html, 'utf-8');
    console.log('Newsletter generated and saved to newsletter.html');
    sendEmail(html, process.env.RECIPIENT_EMAIL)

}