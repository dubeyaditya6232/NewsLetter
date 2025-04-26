const getCurrentMonthAndYear = () => {
    const date = new Date();
    const options = { month: 'long', year: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

export const generateHtmlTemplate = (articles, mainKeyword, generatePoints) => {
    let html = `
<div class="container">
    <h1>GenAI Weekly Digest</h1>
    <p><em>Happenings in Generative AI: ${getCurrentMonthAndYear()}</em></p>
    <div class="digest-flex">
        <!-- Left Column: 30% -->
        <div class="side-section">
            <div class="did-you-know">
                <h3>💡 Did You Know?</h2>
                <strong>${mainKeyword}</strong> is a trending topic in GenAI this week. Stay tuned for more insights!
                <p>${generatePoints}</p>
            </div>
            <div class="whats-next">
                <h3>🔮 What's Next?</h2>
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
h3 { color: #234e70; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-top: 0; }
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
@media (max-width: 600px) {
    .digest-flex { flex-direction: column; }
    .side-section, .main-section { flex: 1 1 100%; }
    .container { padding: 14px; }
}
</style>
`;
    return html;
}