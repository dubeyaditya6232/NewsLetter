import { createCanvas } from 'canvas';
import fs from 'fs';

export function generateImageTemplate(articles, mainKeyword, doYouKnowPoints) {
    // Canvas setup
    const height = 1200, width = 800;
    const canvas = createCanvas(width, height);
    const ctx = canvas.getContext('2d');

    // Layout
    const section1Width = width * 0.7;
    const section2Width = width * 0.3;
    const gapHeight = 10; // gap between Section 2 & 3

    // Helper function to wrap text and measure height
    function wrapTextGetHeight(text, x, y, maxWidth, lineHeight, font) {
        ctx.font = font;
        const words = text.split(' ');
        let line = '';
        let height = 0;
        let lines = [];
        for (let n = 0; n < words.length; n++) {
            let testLine = line + words[n] + ' ';
            let testWidth = ctx.measureText(testLine).width;
            if (testWidth > maxWidth && n > 0) {
                lines.push(line);
                height += lineHeight;
                line = words[n] + ' ';
            } else {
                line = testLine;
            }
        }
        lines.push(line);
        height += lineHeight;
        // Now render:
        let drawY = y;
        for (let l of lines) {
            ctx.fillText(l, x, drawY);
            drawY += lineHeight;
        }
        return height;
    }

    // --- Measure Section 2 ("Did You Know?") height ---
    const section2TitleFont = "bold italic 18px Arial";
    const section2BodyFont = "italic 14px Arial";
    ctx.font = section2TitleFont;
    const sec2TitleHeight = 30;
    const sec2TitleY = 50;

    ctx.font = section2BodyFont;
    const sec2TextY = sec2TitleY + sec2TitleHeight + 10;
    // measure height only, so not drawing yet
    function measureTextHeight(text, maxWidth, lineHeight, font) {
        ctx.font = font;
        const words = text.split(' ');
        let line = '';
        let height = 0;
        for (let n = 0; n < words.length; n++) {
            let testLine = line + words[n] + ' ';
            let testWidth = ctx.measureText(testLine).width;
            if (testWidth > maxWidth && n > 0) {
                height += lineHeight;
                line = words[n] + ' ';
            } else {
                line = testLine;
            }
        }
        height += lineHeight;
        return height;
    }
    const sec2BodyHeight = measureTextHeight(doYouKnowPoints, section2Width - 40, 26, section2BodyFont);
    const section2Height = sec2TitleHeight + 10 + sec2BodyHeight + 40; // Add some padding

    // --- Section 3 ("What's Next") height ---
    const section3TitleFont = "bold 18px Arial";
    const section3BodyFont = "14px Arial";
    ctx.font = section3TitleFont;
    const sec3TitleHeight = 30;
    const sec3TitleY = section2Height + gapHeight + 30;

    const section3Text = "Follow for the latest updates and news. Our AI-curated content brings you the most relevant information every Week.";
    ctx.font = section3BodyFont;
    const sec3TextY = section2Height + gapHeight + 50;
    const sec3BodyHeight = measureTextHeight(section3Text, section2Width - 40, 26, section3BodyFont);
    const section3Height = sec3TitleHeight + 10 + sec3BodyHeight + 40; // Add some padding

    // --- Draw Section 1 ---
    ctx.fillStyle = "#f0f0f0";
    ctx.fillRect(0, 0, section1Width, height);

    // --- Draw Section 2 ---
    ctx.fillStyle = "#cce5ff";
    ctx.fillRect(section1Width, 0, section2Width, section2Height);

    // Section 2 shadow & border
    ctx.shadowColor = 'rgba(0, 0, 0, 0.10)';
    ctx.shadowBlur = 6;
    ctx.shadowOffsetX = 3;
    ctx.shadowOffsetY = 3;
    ctx.strokeStyle = "#6699cc";
    ctx.lineWidth = 2;
    ctx.strokeRect(section1Width, 0, section2Width, section2Height);
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;

    // --- Draw Section 3 ---
    // Section 3 starts at y = section2Height + gapHeight
    ctx.fillStyle = "#b3ffd9";
    ctx.fillRect(section1Width, section2Height + gapHeight, section2Width, section3Height);

    // Section 3 border
    ctx.strokeStyle = "#66cc99";
    ctx.lineWidth = 2;
    ctx.strokeRect(section1Width, section2Height + gapHeight, section2Width, section3Height);

    // --- Section 1: News Articles (with summary) ---
    ctx.fillStyle = "#222";
    ctx.font = "bold 22px Arial";
    ctx.fillText("Last Week Top News on GEN AI", 30, 60);

    let y = 110;
    const maxArticleHeight = height - 120;
    for (let idx = 0; idx < articles.length; idx++) {
        const article = articles[idx];

        if (y > maxArticleHeight) break;

        ctx.font = "bold 18px Arial";
        const titlePrefix = `${idx + 1}. `;
        ctx.fillText(titlePrefix, 30, y);

        const titleX = 30 + ctx.measureText(titlePrefix).width;
        const titleHeight = wrapTextGetHeight(article.title, titleX, y, section1Width - 60, 30, "bold 18px Arial");
        y += titleHeight + 5;

        if (article.summary) {
            const summaryHeight = wrapTextGetHeight(
                article.summary,
                50,
                y,
                section1Width - 80,
                24,
                "14px Arial"
            );
            y += summaryHeight;
        }
        y += 15; // Spacing between articles
    }

    // --- Section 2: Did You Know ---
    ctx.fillStyle = "#333";
    ctx.font = section2TitleFont;
    ctx.fillText("Did You Know?", section1Width + 20, 50);

    ctx.font = section2BodyFont;
    wrapTextGetHeight(doYouKnowPoints, section1Width + 20, 90, section2Width - 40, 26, section2BodyFont);

    // --- Section 3: What's Next ---
    ctx.fillStyle = "#333";
    ctx.font = section3TitleFont;
    ctx.fillText("What's Next", section1Width + 20, section2Height + gapHeight + 30);

    ctx.font = section3BodyFont;
    wrapTextGetHeight(
        section3Text,
        section1Width + 20,
        section2Height + gapHeight + 50,
        section2Width - 40,
        26,
        section3BodyFont
    );

    // Save to file
    const buffer = canvas.toBuffer('image/png');
    fs.writeFileSync('./assets/images/newsletter.png', buffer);
    return buffer;
}
