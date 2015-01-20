import time
from math import isinf

from indico.util.console import colored


class Benchmark(object):
    """Simple benchmark class

    Can be used manually or as a contextmanager:

    with Benchmark() as b:
        do_stuff()
    b.print_result()
    """
    def __init__(self, start=False):
        self._start_time = None
        self._end_time = None
        if start:
            self.start()

    def start(self):
        self._start_time = time.time()
        return self

    def stop(self):
        self._end_time = time.time()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __float__(self):
        if self._start_time is None:
            return float('-inf')  # not started
        elif self._end_time is None:
            return float('inf')  # not finished
        return self._end_time - self._start_time

    def __str__(self):
        duration = float(self)
        if isinf(duration):
            return str(duration)
        return '{:.05f}'.format(duration)

    __repr__ = __str__

    def print_result(self, slow=float('inf'), veryslow=float('inf')):
        duration = float(self)
        if duration == float('-inf'):
            print colored('skipped', 'blue', attrs=['bold'])
        elif duration == float('inf'):
            print colored('running', 'red')
        elif duration >= veryslow:
            print colored(str(self), 'red', attrs=['bold'])
        elif duration >= slow:
            print colored(str(self), 'yellow', attrs=['bold'])
        else:
            print colored(str(self), 'green', attrs=['bold'])
