import config


class DonaterAdapter:

    def __init__(self):
        pass

    def get_donaters(self):
        """
        Get donaters from file

        Returns:
            list[str]: list of donaters
        """

        with open(config.WHITE_LIST_FILE_NAME, 'r') as file:
            donaters = file.read().splitlines()
        
        return donaters
    
    def is_donater(self, user):
        """
        Check if user is donater

        Args:
            user (str): user

        Returns:
            bool: True if user is donater
        """

        donaters = self.get_donaters()

        if user in donaters:
            return True
        
        return False
