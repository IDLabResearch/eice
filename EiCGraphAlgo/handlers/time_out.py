from __future__ import with_statement
from contextlib import contextmanager
import signal

class TimeoutException(BaseException): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise (TimeoutException, "Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
