##################################################################################################
'''
    This module provides a method for blocking until an OS signal is sent.
'''
##################################################################################################

import signal
import time
from .debugging import app_logger as log

class ShutdownWatcher:
    ''' 
    ShutdownWatcher listens for the signals: SIGINT, SIGTERM.
    When the app is signaled to shutdown it sets should_continue to False.

    Example usage:

    with ShutdownWatcher() as Watcher:
            watcher.serve_forever() # <-- Blocks until signaled.
    '''
    
    def __init__(self):
        # use this boolean property to determine if process should continue to loop, or stop
        self.should_continue = True

        # next we use signal library to register the OS signals that we listen for
        # We are going to listen for SIGTERM and SIGINT
        # If we recieve either of those we are going to call the exit function
        for s in [signal.SIGTERM, signal.SIGINT]:
            # note that we are not calling the exit method here
            # we are just passing in a reference to it 
            # that the signal handler is going to call for us when it recieves one of these signals
            signal.signal(s, self.exit)



    # to make a class into a context manager 
    # we need to implement the magic methods dunder enter and dunder exit
    # dunder just stands for double underscore
    # these allow us to perform some basic set up and tear down

    #    with ShutdownWatcher() as Watcher:
    #        watcher.serve_forever() # <-- Blocks until signaled.

    # the with keyword sets off the __enter__ method.
    # because we're returning self, it also allows us to use the 'as' keyword as a reference to the ShutdownWatcher itself

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        # all this does is call our exit method
        # this is called by the with method, which means that anything inside the block of code 
        # for the with statement is also stopped???
        # either way this is what ends the with statment and allows the function to proceed
        # or maybe this just helps with exception handling, with cleaner code
        # remember try and catch is embedded inside of the with keyword 
        self.exit()

    def serve_forever(self):
        # this is the implementation of our core functionality 
        while self.should_continue == True:
            time.sleep(0.1)
    
    def exit(self, *args, **kwargs):
        # this simply sets the should continue value to false
        # the args and kwargs are from the with keyword or whatever handles the magic methods 
        self.should_continue = False


