import dotenv from "dotenv";
dotenv.config();
import fs from "fs";
import { GoogleGenAI } from "@google/genai";
import { sendEmail } from "./mail/mail.js";
import { fetchFromGNews, fetchFromNewsAPI } from "./articles.js";

// console.log("Google GenAI API Key:", process.env.GOOGLE_API_KEY);

const ai = new GoogleGenAI({ apiKey: process.env.GOOGLE_API_KEY });

const genAI_call = async () => {
    const response = await ai.models.generateContent({
        model: "gemini-2.0-flash",
        contents: "Explain how AI works in a few words",
    });
    console.log(response.text);
}

async function rankArticlesWithLLM(articles) {
    const prompt = `You are an expert AI assistant that filters and ranks news articles about generative AI.
    Only retain articles that highlight genuine technological advancements or research.
    Return ONLY a valid JSON array sorted by importance with keys: title, summary, url. Do not include any explanations or headers. 
    Rank the most important articles first.Remove articles which have less than 20 words in the summary.
    Here are the articles:
  ${articles.map((a, i) => `${i + 1}. Title: ${a.title}\nURL: ${a.url}`).join('\n\n')}
  Return the top articles in a JSON array sorted by importance with keys: title, summary, url.`;

    const response = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=' + process.env.GOOGLE_API_KEY, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            contents: [{ role: 'user', parts: [{ text: prompt }] }]
        })
    });

    const data = await response.json();
    const content = data.candidates?.[0]?.content?.parts?.[0]?.text;

    try {
        const jsonMatch = content.match(/\[.*\]/s);
        if (jsonMatch) {
            return JSON.parse(jsonMatch[0]).slice(0, 50);
        } else {
            throw new Error('No valid JSON found in Gemini response.');
        }
    } catch (err) {
        console.error('Failed to parse Gemini response:', content);
        console.error('Error:', err.message);
        return articles.slice(0, 50);
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
        fetchFromGNews()
    ]);
    const allArticles = [...newsApiArticles, ...gnewsArticles];
    const uniqueArticles = Array.from(new Map(allArticles.map(a => [a.url, a])).values());
    uniqueArticles.filter(a => a.summary !== 'No summary available.');
    const rankedArticles = await rankArticlesWithLLM(uniqueArticles);
    return rankedArticles;
}

let articles = await fetchNews()
console.log('Fetched articles:', articles.length);
const template = fs.readFileSync('./mail/newsletter_template.html', 'utf-8');
if (articles.length === 0) {
    console.log('No articles found. Exiting...');
} else {
    const html = populateTemplate(template, articles);
    sendEmail(html, process.env.RECIPIENT_EMAIL)
}