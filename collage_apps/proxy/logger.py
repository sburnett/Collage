import os.path
import logging
from logging.handlers import TimedRotatingFileHandler

import pdb

def get_logger(name, filename):
    logger = logging.getLogger(name)

    directory = os.environ.get('COLLAGE_LOGDIR')
    if directory is not None and os.path.isdir(directory):
        filename = os.path.join(directory, filename + '.log')
        handler = TimedRotatingFileHandler(filename, when='D')
        formatter = logging.Formatter("[%(asctime)s] (%(name)s) %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    return logger
