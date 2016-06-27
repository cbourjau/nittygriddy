class AlienTokenError(Exception):
    """
    An exception which is raised for alien token errors
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
