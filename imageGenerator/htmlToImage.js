import puppeteer from 'puppeteer';
import fs from "fs";
import { generateHtmlTemplate } from '../mail/generateHtml.js';

export default async function generateNewsletterImage(articles, mainKeyword, didYouKnow){
    const browser = await puppeteer.launch({headless: 'new'});
    const page = await browser.newPage();
    await page.setViewport({ width: 900, height: 1200 });
    // Generate HTML content
    await page.setContent(generateHtmlTemplate(articles, mainKeyword, didYouKnow));
    const imageBuffer = await page.screenshot({
        type: 'jpeg',
        quality: 90,
        fullPage: true
    });
    await browser.close();
    fs.writeFileSync('./assets/images/newsletter.jpeg', imageBuffer, 'binary', (err) => {
        if (err) throw err;
        console.log('Image saved as newsletter.jpeg');
    });
    return imageBuffer;
}