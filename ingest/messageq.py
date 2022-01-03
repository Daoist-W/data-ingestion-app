##################################################################################################
'''
This module provides us with a drainable multiprocess aware message queue.
'''
##################################################################################################

from multiprocessing import Event, Queue
from multiprocessing.managers import BaseManager
from queue import Empty
from typing import Any, List

from .debugging import app_logger as log


class QueueWrapper(object):

    def __init__(self, name: str, q: Queue = None, prevent_writes: Event = None):
        self.name = name
        # set to either a queue that is passed into the constructor, or a multiprocessing queue that we create
        # this is just a fancy way of saying that if the value passed in q exists, use it, otherwise create one
        self.q = q or Queue

        # we need a way to signal when the queue is drained, and for some reason simply using a boolean wouldn't
        # work out how we'd expect it to
        # an instance of this class is going to be created by a parent process 
        # then it is going to be pickled and passed to our worker process
        # pickling is a python specific serialisation format which makes it easy to save the state of an object
        # when this process happens, it is going to create a *copy* of the original instance
        # so if we create an instance and pass it to two processes, we would have 3 instances 
        # since queue is multi-process aware, those copies are going to use a proxy that python creates for us to
        # automatically interact with the Queue.
        # for values that are not multiprocess aware, those values don't sync up automatically
        # boolean values would be independant of the multiprocess Queue module 

        # we need a mechanism that is process aware to determine if the queue is writable
        # we solve this by using a multiprocessing verion of theading.Event, imported from multiprocessing
        # the idea is that Event is basically a boolean value, in that it is either "set" or "unset" 
        # one that can be listened to by other processes
        # once this value is set/assigned, any process subscribed to listen will be notified
        # when the event is set, it is set for every process listening
        self._prevent_writes = prevent_writes or Event()

    def connect(self): # can be ignored, wasn't used in tutorial part one
        '''
        Connect to multiprocessing.Queue
        Used by clients attempting to connect to the Queue via a proxy
        '''
        # self.q.connect()
        pass

    def get(self) -> Any:
        '''
        This call blocks until it gets a message from the queue.
        If the queue is drained, it returns the sentinel string STOP
        If the queue is closed while this call is blocking, it'll return STOP
        '''
        # if the queue is drained, meaning not writable and/or empty
        # this tells whatever code is calling get that this queue is no longer usable
        if self.is_drained:
            return 'STOP'

        '''
        By default, the get method for the multiprocessing Queue is a blocking call. 
        So it's going to wait until it takes something off of the queue.
        Because it's blocking until there's something on the queue, it could get interrupted.
        '''
        try:
            return self.q.get() # this is not a recursive function, it is a multiprocessing method from Queue
        except:
            log.info('q.get() interrupted')
            return 'STOP'
    
    # for our put method, we only want to put messages  onto the queue if the queue is writable
    # the teacher likes to use a debug level logger for cases like these
    # we don't want to log every single put() into the production logs, however in development these
    # logs can be helpful when we set the log level to debug
    def put(self, obj: object):
        if self.is_writable:
            log.debug('adding message to queue')
            self.q.put(obj)
    
    # all this does is make it more convenient to use self.put() by passing lists into function
    def put_many(self, objs: List[object]):
        for obj in objs:
            self.put(obj)
    
    def prevent_writes(self):
        '''
        Prevent external writes to the queue.
        This is useful for shutting down, or dealing with backpressure.
        '''
        # the way we prevent writes is by calling set on our prevent writes event
        # we need to make prevent write a private attribute (internal use only) so we add an underscore
        # once this instance is set, any tasks using this queue will know that it is not writable
        log.debug(f'preventing writes to {self.name} queue')
        self._prevent_writes.set()

    @property
    def is_writable(self) -> bool:
        '''Read-only property indicating if the queue is writable'''
        # the logic is simply to check if the event is not set
        return not self._prevent_writes.is_set()
    
    @property
    def is_drained(self) -> bool:
        '''If the queue is not writable and is empty whilst the queue is draining'''
        # simple check for the required conditions
        return not self.is_writable and self.empty


    @property
    def empty(self) -> bool:
        '''Read only property indicating if the queue is empty'''
        # this uses the multiprocessing.Queue method to check if the queue is empty
        return self.q.empty()

# we don't need to add or change anything for this object, simply inherit it with QueueManager
class QueueManager(BaseManager):
    pass


# the way a manager exposes functionality to remote processes
# is that we register functions that we want to share

# this register manager function accepts a name and an optional queuewrapper 
# if the QueueWrapper exists, we call the BaseManager's register method, passing in the name
# and a lambda function that returns a QueueWrapper
# this is going to allow any process that has access to call any public method in that particular QueueWrapper
# it will also have access to its properties
def register_manager(name: str, queue: QueueWrapper = None):
    if queue:
        # used by backend 
        QueueManager.register(name, callable=lambda: queue)
    else:
        # used by frontend
        # the reason for this is that if a QueueWrapper isn't passed in as an argument
        # the backend is going to create a QueueWrapper and register it so that it is accessible to the front end
        # so the backend needs to provide a queue and 
        # the front end is going to connect to the created QueueWrapper
        # so the front doesn't need to pass in a value for 'queue' since it is the one consuming it
        # however both the front and back ends need to register the name, so we use same function for both
        QueueManager.register(name)


# this function requires a port manager to bind the QueueManager to
# in testing with ubuntu it was found that if we use local host for the address, interactions were
# extremly slow, like 1 per second
# so we should use another port, like the one specified below
# this is the default host for the inet so it is a bit weird to use it? why not an empty address?

def create_queue_manager(port: int) -> QueueManager:
    '''
    Binds to 127.0.0.1 on the given port.
    Using localhost on at least Debian systems results in extremely slow put() calls.
    '''
    # by binding to 127.0.0.1 we can limit access/connections to only processes that are running on the same host
    # and by using 'authkey' we can add another layer of protection that requires connections to provide this key
    # in summary these functions will allow our processes to share a QueueWrapper with the front end 
    return QueueManager(address=('127.0.0.1', port), authkey=b'ingestbackend')
    