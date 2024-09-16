import re
import config
import tiktoken


class UtilityAdapter:
    """
    Text adapter class
    """

    def __init__(self):
        pass

    def is_message_to_bot(self, message):
        """
        Check if message is to bot
        """

        chat_title = message.chat.title

        for word in message.text.split():

            if (word.lower() in config.KEYWORDS) or (chat_title is None):

                return True

        return False

    def strip_message_text(self, message):
        """
        Strip message text from keywords
        """

        message = message.lower()

        for word in config.KEYWORDS:
            message = message.replace(word, '')

        return message.strip()

    def get_links(self, text: str):
        """
        Get link from text

        Args:
            text (string): text

        Returns:
            list[urls]: list of urls
        """

        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls = url_pattern.findall(text)

        links = []
        for url in urls:
            links.append(url)
        
        return links

    def num_tokens_from_string(self, string: str, encoding_name: str) -> int:
        """
        Get number of tokens from string

        Args:
            string (str): text for encoding
            encoding_name (str): model name

        Returns:
            int: number of tokens
        """

        # encoding = tiktoken.encoding_for_model(encoding_name)
        encoding = tiktoken.get_encoding('cl100k_base')
        num_tokens = len(encoding.encode(string))
        return num_tokens
    
    def format_number(self, n):
        """
        Format number

        Args:
            n (int): number

        Returns:
            str: formated number
        """        
        return "{:,}".format(n)
