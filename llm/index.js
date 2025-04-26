

export const doYouKnow = async (keyword) => {
    const prompt = `You are an expert AI assistant that generates a "Did You Know?" section for a newsletter.
    Generate a fun fact or interesting information about "${keyword}" in the context of generative AI. 1-2 sentences only.
    Do not include any explanations or headers and do not use the phrase "Did you know?".`;
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


const maxRetries = 3;
export const rankArticlesWithLLM = async (articles) => {
    const prompt = `You are an expert AI curator specializing in Generative AI news and research.
    Filter, enhance, and rank the provided articles according to these criteria:
    FILTERING RULES:
    1. Keep articles that discuss:
       - Technological breakthroughs in Generative AI
       - Research papers and findings with clear technical details
       - Major industry developments with concrete impact
       - Novel applications with specific use cases
    2. Remove articles that:
       - Have titles in question format
       - Are opinion pieces without technical substance
       - Have summaries shorter than 20 words
       - Are primarily about business/stock market
       - Contain version numbers without context
       - Lack clear technical description or impact
    ENHANCEMENT REQUIREMENTS:
    - For research papers: Include methodology and key findings
    - For industry news: Include technical implications and impact
    - For applications: Include implementation details and benefits
    RANKING CRITERIA:
    - Technical depth and innovation (40%)
    - Practical impact and applicability (30%)
    - Validation and credibility (20%)
    - Timeliness and relevance (10%)
    Here are the articles for review:
    ${articles.map((a, i) => `${i + 1}. Title: ${a.title}\nURL: ${a.url}`).join('\n\n')}
    Return the filtered and ranked articles in this JSON format:
    [{
        "title": "Title of the article",
        "summary": "Comprehensive technical summary (minimum 40 words)",
        "url": "URL of the article"
    }]`

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