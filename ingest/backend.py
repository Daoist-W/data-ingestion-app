###############################################################################
'''
    This module handles the creation of worker and saver processes.
    Worker processes get items from a message queue and process them with a
    DataProcessor(). The processed data is put on a different message queue 
    which is consumed by the saver.
    Saver processes get items from a message queue and saves it to Firestore.
    INPUT QUEUE           Workers      OUTPUT QUEUE
    [................] -> Worker() --> [................] -> Saver() --> Firestore
                      |_> Worker() _|                    |_> Saver() _|
                      |_> Worker() _|                    |_> Saver() _|
                      |_> Worker() _|
'''
###############################################################################
import os
import signal
from collections import defaultdict
from multiprocessing import Process
from typing import Dict, List, Tuple

from .debugging import app_logger as log
from .messageq import QueueWrapper, create_queue_manager, register_manager
from .models import ProcessedPost
from .persistence import get_database_client, persist, persist_no_op
from .processor import DataProcessor
from .shutdownwatcher import ShutdownWatcher


class Worker(Process):
    '''Worker is a multiprocessing.Process that is responsible for 
    fetching data from the input queue and extracting known entities.
    '''

    def __init__(self, inq: QueueWrapper, outq: QueueWrapper, cache_size: int = 25_000):
        # initially we ignored everything related to caching
        # we first set up the reference variables
        # the colons are just annotations again
        self.iq: QueueWrapper = inq
        self.oq: QueueWrapper = outq 

        # we also need to make sure that we call the init method from our super class
        super(Worker, self).__init__()

    def shutdown(self, *args):
        log.info('shutting down worker')

        # now we are going to enqueue a stop message 
        # notice that we are calling the put method of the Queue class, not QueueWrapper
        self.iq.q.put('STOP')

        # The reason for this is that out QueueWrapper does not allow writes after 
        # prevent_writes is called, so we circumvent it and access the underlying Queue instance
        # now when the process is sent a SIGTERM, is going to enqueue a 'STOP' message




    def count(self, incr_num: int = None) -> int:
        '''Count increments the counter by the given value and returns the total.
        If no value is given, the current count is returned.
        '''
        return 0

    def reset_cache(self):
        pass

    def cache(self, msg: ProcessedPost) -> int:
        '''Caches messages until flush_cache is called.
        Returns the number of currently cached values.
        '''
        return 0

    def flush_cache(self):
        pass

    def run(self):
        # Register the shutdown handler for this process.
        # this allows us to shutdown the worker more gracefully than just stopping
        # the process mid work

        # SO, whenever we send the signal SIGTERM to these child processes
        # they're going to run the shutdown method
        signal.signal(signal.SIGTERM, self.shutdown)

        # Only the worker processes need to use the data processor.
        # The data processor uses Spacy for its processing.
        # Spacy can take up a bit of memory when loaded. The amount depends on
        # which model is used. If we instantiate in __init__ the process
        # that creates Workers ends up using more memory than needed.
        processor = DataProcessor()

        # self.iq.get() is a blocking call.
        # This will repeatedly call get and wait for an object to be
        # pulled from the queue until the get call returns the sentinel 'STOP'

        # this is the uncached method 
        for msg in iter(self.iq.get, 'STOP'):
            self.oq.put(processor.process_message(msg))

        '''
            see now my understanding is it continuously get() messages from input queue iq and stores them
            inside the output queue 'oq' until it comes across the message 'STOP' from the input queue
            which has been put in place by the shutdown method directly into the underlying q.
            ONCE that message is matched, the loop stops
        '''

        # # this is the cached method 
        # for msg in iter(self.iq.get, 'STOP'):
        #     if self.cache(processor.process_message(msg)) == self._cache_size:
        #         self.flush_cache()
        # # Leaving the process with a status code of 0, if all went well.
        # self.flush_cache()
        exit(0)


class Saver(Process):
    '''Saver pulls messages off the queue and passes the message and client to the persist_fn.'''
    # arguments are the output queue, the database client, and the persistance function 
    def __init__(self, q: QueueWrapper, client, persist_fn):
        # first thing we check is that the persistence function is callable
        # we need our code to fail early if we recieve something we don't expect
        # this checks if the function is even callable, if not it stops before doing real work
        assert callable(persist_fn)
        self.q: QueueWrapper = q
        self.client = client
        self.persist_fn = persist_fn

        # we also need to make sure that we call the init method from our super class
        super(Saver, self).__init__()

    def shutdown(self, *args):
        log.info('shutting down saver')
        self.q.q.put('STOP')

    def run(self):
        # same as for worker
        signal.signal(signal.SIGTERM, self.shutdown)

        # see worker notes 
        # this loop has been modified, the messages we get() from our queue are going to be
        # passed to our persistence function instead
        # this function accepts a client and then some additional arguments
        # client, pubname, collname, doc_id, document_dict
        # at the moment (sprint 5 part 1) the 'msg' is a dictionary returned by processor.process
        # we are going to change that into a tuple that matches the arguments required for persist
        for msg in iter(self.q.get, 'STOP'):
            log.info(msg)
            self.persist_fn(self.client, *msg)

        exit(0)


def start_processes(proc_num: int, proc: Process, proc_args: List[object]) -> List[Process]:
    # proc_num is the number of processes to be initialised
    # proc is the class of the process, either worker or saver
    # proc_args is a list that will be passed into each instantiated process
    '''Instantiates and starts the given process.'''
    log.info(f"initializing {proc_num} worker processe(s)")
    # below is an example of list comprehension 
    # this code block says reference variable is assigned the following
    # instantiate Process(*proc_args) in a loop, proc_num number of times
    procs = [proc(*proc_args) for _ in range(proc_num)]
    # this code block starts all of the listed processes in procs, then returns them 
    # we return the list so that we have a reference to them when we want to shut them down later
    for p in procs:
        p.start() # start calls the run method
    return procs


def shutdown(q: QueueWrapper, procs: List[Process]):
    '''Shuts down the given processes using the following steps:
    1.) Disable writes to the given QueueWrapper
    2.) Send SIGTERM signals to each of the given processes
    3.) Calls join on the procs, blocking until they complete.
    '''
    # we need to set prevent_writes() so that we are no longer writing new messages to queue
    q.prevent_writes()
    # logging 
    log.info(f"sending SIGTERM to processes")
    # next we send each of the processes a SIGTERM signal using LIST COMPREHENSION 
    # processes 'p' in procs have all inherited the methods and properties of Process
    # so this signal them to execute their shutdown method 
    [os.kill(p.pid, signal.SIGTERM) for p in procs]
    log.info(f"joining processes")
    # join makes sure the child processes are all complete/shutdown before the parent
    # process is shut down
    [p.join() for p in procs]


def register_shutdown_handlers(queues, processes):
    '''Create shutdown handlers to be kicked off on exit.'''
    def shutdown_gracefully():
        for args in zip(queues, processes):
            shutdown(*args)

    import atexit
    atexit.register(shutdown_gracefully)


def main():
    pcount = (os.cpu_count() - 1) or 1
    parser_arguments = [
        ('--iproc_num', {'help': 'number of input queue workers', 'default': pcount, 'type': int}),  # noqa
        ('--oproc_num', {'help': 'number of output queue workers', 'default': pcount, 'type': int}),  # noqa
        ('--iport', {'help': 'input queue port cross proc messaging', 'default': 50_000, 'type': int}),  # noqa
        ('--no_persistence', {'help': 'disable database persistence', 'action': 'store_true'}),  # noqa
        ('--agg_cache_size', {'help': 'aggregator cache size', 'default': 25_000, 'type': int}),  # noqa
    ]

    import argparse
    parser = argparse.ArgumentParser()
    for name, args in parser_arguments:
        parser.add_argument(name, **args)

    args = parser.parse_args()

    iproc_num = args.iproc_num
    oproc_num = args.oproc_num
    iport = args.iport
    cache_sz = args.agg_cache_size
    # A tuple containing the db client and method for persisting message
    # For testing, the no_persistence flag allows us to use a null client with a no op function.
    if args.no_persistence:
        persistable = (None, persist_no_op)
    else:
        persistable = (get_database_client(), persist)

    # Setup the input queue, aggregate queue, and output queue
    iq = QueueWrapper(name="iqueue")
    oq = QueueWrapper(name="oqueue")

    # Register and start the input queue manager for remote connections.
    # This allows the frontend to put messages on the queue
    register_manager("iqueue", iq)
    iserver = create_queue_manager(iport)
    iserver.start()

    # Start up the worker/saver processes
    iprocs = start_processes(iproc_num, Worker, [iq, oq, cache_sz])
    oprocs = start_processes(oproc_num, Saver, [oq, *persistable])

    # Setup the shutdown handlers to gracefully shutdown the processes.
    register_shutdown_handlers([iq, oq], [iprocs, oprocs])

    with ShutdownWatcher() as watcher:
        watcher.serve_forever()
    exit(0)