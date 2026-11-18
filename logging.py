import logging
from logging.handlers import RotatingFileHandler

LOG_FILE = "busbidder.log"

# for logs
def get_logger(name="busbidder"):
    logger = logging.getLogger(name)
    if logger.handlers:            
        return logger
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(module)s | %(message)s"))
    logger.addHandler(handler)
    return logger