import logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] - [%(levelname)s] - %(message)s')

class Log:
    def __init__(self) -> None:
        '''
        This class is a wrapper around the logging module.
        '''
        pass

    @staticmethod
    def error(message: str):
        logging.error(message)

    @staticmethod
    def debug(message: str):
        logging.debug(message)

    @staticmethod
    def info(message: str):
        logging.info(message)