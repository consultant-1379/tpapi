import logging
import TPAPI

class TPAPILogger(object):
    
    def __init__(self,loglevel='debug'):
        '''TPAPI Logger Object'''
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level:' + str(loglevel))
        logger = logging.getLogger('TPAPI')
        logger.setLevel(level=numeric_level)
        fh = logging.FileHandler('TPAPI.log')
        fh.setLevel(level=numeric_level)
        ch = logging.StreamHandler()
        ch.setLevel(level=numeric_level)
        formatter = logging.Formatter('%(asctime)s-%(levelname)s-%(name)s-%(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
        logger.info('Starting Logging')
 


