import signal
import sched
import time
import os
import pytest
from ingest.shutdownwatcher import ShutdownWatcher
from unittest.mock import MagicMock


def teardown_function():
    """Remove handlers from all loggers"""
    import logging

    loggers = [logging.getLogger()] + \
        list(logging.Logger.manager.loggerDict.values())
    for logger in loggers:
        handlers = getattr(logger, "handlers", [])
        for handler in handlers:
            logger.removeHandler(handler)

# this creates a new instance for each test
@pytest.fixture(scope="function")
def watcher():
    return ShutdownWatcher()


@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
    # this line above runs the below test twice, changing the value of "sig" to signal.SIGINT, then signal.SIGTERM
def test_shutdown_manager(watcher, sig):
    # check that should continue is equal to True for new instances, this should always be the case 
    assert watcher.should_continue

    # be design, no process after the shutdownwatcher is set to serve_forever() should be allowed to run
    # so we need to schedule sending out the signal to terminate the server_forever() method ahead of time
    s = sched.scheduler(time.time, time.sleep)
    # Shedule the signal to be sent 0.1 seconds after s.run() is called.
    s.enter(0.1, 1, lambda: os.kill(os.getpid(), sig))

    with watcher as w:
        s.run() # this will send a kill signal after 0.2 seconds
        w.serve_forever() # as soon as this starts to run, within 0.2 seconds it will terminate due to the signal

    assert not watcher.should_continue