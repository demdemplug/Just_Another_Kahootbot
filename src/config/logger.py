import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# StreamHandler for logging to the console
ch = logging.StreamHandler()
ch.setLevel(logging.INFO) 
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# FileHandler for logging to a file
fh = logging.FileHandler('./app.log')  # Log file name
fh.setLevel(logging.DEBUG)  # You can set the level for file logging
fh.setFormatter(formatter)
logger.addHandler(fh)

