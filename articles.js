import axios from 'axios';

function getLast7DaysRange() {
    const today = new Date();
    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(today.getDate() - 7);

    const fromDate = sevenDaysAgo.toISOString().split('T')[0];
    const toDate = today.toISOString().split('T')[0];

    return { fromDate, toDate };
}

export const fetchFromNewsAPI = async () => {
    const { fromDate, toDate } = getLast7DaysRange();

    const url = `https://newsapi.org/v2/everything?q=generative+AI+OR+LLM+OR+OpenAI&from=${fromDate}&to=${toDate}&sortBy=publishedAt&language=en&pageSize=25&apiKey=${process.env.NEWS_API_KEY}`;
    const response = await axios.get(url);
    if (response.status !== 200) {
        console.error('Error fetching from NewsAPI:', response.statusText);
        return [];
    }
    if (!response?.data?.articles) {
        console.error('No articles found in NewsAPI response');
        return [];
    }
    console.log('Articles fetched from NewsAPI:', response.data.articles.length);
    return response?.data.articles.map(article => ({
        title: article.title,
        url: article.url,
        summary: article.description || 'No summary available.'
    }));
}

export const fetchFromGNews = async () => {
    const { fromDate, toDate } = getLast7DaysRange();
    const url = `https://gnews.io/api/v4/search?q=generative%20AI&lang=en&from=${fromDate}&to=${toDate}&max=25&token=${process.env.GNEWS_API_KEY}`;
    const response = await axios.get(url);
    if (response.status !== 200) {
        console.error('Error fetching from GNewsAPI:', response.statusText);
        return [];
    }
    if (!response?.data?.articles) {
        console.error('No articles found in GNewsAPI response');
        return [];
    }
    console.log('Articles fetched from GNewsAPI:', response.data.articles.length);
    return response?.data.articles.map(article => ({
        title: article.title,
        url: article.url,
        summary: article.description || 'No summary available.'
    }));
}