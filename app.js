import dotenv from "dotenv";
dotenv.config();
import fs from "fs";
import { sendEmail } from "./mail/mail.js";
import { fetchFromNewsAPI } from "./articles.js";
import { generateHtmlTemplate } from "./mail/generateHtml.js";
import { extractKeywords } from "./utils/keywordExtractor.js";
import { doYouKnow, rankArticlesWithLLM } from "./llm/index.js";
import { generateImageTemplate } from "./imageGenerator/image.js";
import generateNewsletterImage from "./imageGenerator/htmlToImage.js";


const fetchNews = async () => {
    const newsApiArticles = await fetchFromNewsAPI();
    const rankedArticles = await rankArticlesWithLLM(newsApiArticles);
    fs.writeFileSync('./assets/articles.json', JSON.stringify(newsApiArticles, null, 2), 'utf-8');
    console.log('Articles saved to articles.json');
    return rankedArticles;
}

const main = async () => {
    let articles = await fetchNews()
    console.log('Fetched articles:', articles.length);
    if (articles.length === 0) {
        console.log('No articles found. Exiting...');
    } else {
        const keywords = extractKeywords(articles);
        console.log('Extracted keywords:', keywords);
        const mainKeyword = keywords[0] || 'GenAI';
        console.log('Main keyword:', mainKeyword);
        const doYouKnowPoints = await doYouKnow(mainKeyword);
        console.log('Did you know:', doYouKnowPoints);
        // const html = generateHtmlTemplate(articles, mainKeyword, doYouKnowPoints);
        // fs.writeFileSync('./mail/newsletter.html', html, 'utf-8');
        // console.log('Newsletter generated and saved to newsletter.html');
        // const imageBuffer = generateImageTemplate(articles, mainKeyword, doYouKnowPoints)
        const imageBuffer = await generateNewsletterImage(articles, mainKeyword, doYouKnowPoints)
        sendEmail(null,imageBuffer, process.env.RECIPIENT_EMAIL);
    }
}

main().catch(err => {
    console.error('Error in main function:', err.message);
});

