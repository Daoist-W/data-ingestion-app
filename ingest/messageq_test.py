import pytest
from queue import Queue
from .messageq import QueueWrapper
from unittest.mock import MagicMock

def teardown_function(): 
    # this is to suppress an error to do with multiprocessing in pytest
    # can be safely ignored /  beyond current scope
    """Remove handlers from all loggers"""
    import logging
    loggers = [logging.getLogger()] + \
        list(logging.Logger.manager.loggerDict.values())
    for logger in loggers:
        handlers = getattr(logger, 'handlers', [])
        for handler in handlers:
            logger.removeHandler(handler)



# this creates an instance that can be created and called for each test
# saves re-writing code
# pytest calls the fixture with the matching argument name
@pytest.fixture(scope='function')
def queue_wrapper():
    return QueueWrapper('testq', q=Queue())

def test_empty(queue_wrapper): # called from fixture
    assert queue_wrapper.q.qsize() == 0
    assert queue_wrapper.empty
    queue_wrapper.put('message')
    assert queue_wrapper.q.qsize() == 1
    assert not queue_wrapper.empty

# remember, all these functions are built into multiprocessing, we simply creted a wrapper with added logic
def test_get(queue_wrapper):
    queue_wrapper.put('message1') # adding/writing to queue
    queue_wrapper.put('message2') # adding/writing to queue
    assert queue_wrapper.get() == 'message1' # consuming/draining from queue
    assert queue_wrapper.get() == 'message2' # consuming/draining from queue
    assert queue_wrapper.empty

def test_get_with_error_returns_stop(queue_wrapper):
    # This seems like a special class that can simulate specific scenarios
    # here it ensures that when get is called it raises an exception, so we should expect 'STOP' to be returned
    # testing error handling
    queue_wrapper.q.get = MagicMock(side_effect=Exception('failed'))
    assert queue_wrapper.get() == 'STOP'

def test_draining(queue_wrapper):
    assert queue_wrapper.is_writable
    assert queue_wrapper.empty
    queue_wrapper.prevent_writes() # sets is_writable to False
    assert not queue_wrapper.is_writable 
    assert queue_wrapper.is_drained




