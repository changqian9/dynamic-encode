import logging.config
import config
from console import console


# Initialize logger object
def init():
    logging.config.dictConfig(config.LOGGING)
    return logging.getLogger(config.LOGGER_NAME)


def logger_set_console(log):
    for h in log.handlers:
        h.stream = console
        if not isinstance(h, logging.FileHandler):
            # Redirect Console
            h.stream = console


# Create logger object
logger = init()
