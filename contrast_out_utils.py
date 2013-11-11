import logging


# Creates a logger object
def create_logger(name):
    logger = logging.getLogger('contrast_out_connector')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler(filename=name)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)
    return logger

class MD5Error(Exception):
	def __init__(self, value):
		self.value = value
