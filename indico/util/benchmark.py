# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import print_function

import time
from math import isinf

from indico.util.console import cformat


class Benchmark(object):
    """Simple benchmark class.

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
            print(cformat('%{blue!}skipped'))
        elif duration == float('inf'):
            print(cformat('%{red}running'))
        elif duration >= veryslow:
            print(cformat('%{red!}{}').format(self))
        elif duration >= slow:
            print(cformat('%{yellow!}{}').format(self))
        else:
            print(cformat('%{green!}{}').format(self))
