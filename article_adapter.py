from newspaper import Article


class ArticleAdapter:

    url = ""
    article = None

    def __init__(self, url):
        self.url = url
        self.article = Article(url)
        self.article.download()
        self.article.parse()
