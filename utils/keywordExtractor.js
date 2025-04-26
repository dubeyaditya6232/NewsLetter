import natural from 'natural';
const { WordTokenizer, PorterStemmer, TfIdf } = natural;

export const extractKeywords=(articles)=> {
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