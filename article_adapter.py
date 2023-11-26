from newspaper import Article


class ArticleAdapter:
    """
    ArticleAdapter is a class that adapts the Article class from the newspaper library
    """    

    url = ""
    article = None

    def __init__(self, url):
        """
        Constructor for ArticleAdapter class

        Args:
            url (str): url of the article
        """

        self.url = url
        self.article = Article(url)
        self.article.download()
        self.article.parse()
