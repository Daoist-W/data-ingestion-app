##################################################################################################
'''
    This module allows us to have a centralised logger that will be used
    from multiple processes at the same time.
'''
##################################################################################################

from multiprocessing import get_logger
import logging

def logger(level=logging.INFO) -> logging.Logger:
    log = get_logger() # obtain logger, creates something like an unconfigured instance?
    log.setLevel(level) # set logging level 
    handler = logging.StreamHandler() # create a stream handler 
    handler.setFormatter(logging.Formatter( # setting up what information to take in, logging level, time, process/PID, messages
        '%(levelname)s: %(asctime)s - %(process)s - %(message)s'
    )) # set up / configure our formatter 
    log.addHandler(handler) # add handler to log
    return log

# Exposing app_logger to be used by other modules.
app_logger = logger()

print("Annotations: ", logger.__annotations__)