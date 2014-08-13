##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.


from functools import partial

from indico.util.contextManager import ContextManager


def run_after_commit(f):
    """Decorator to delay a function call until after a successful commit when executed within a RH context"""

    def wrapper(*args, **kwargs):
        func = partial(f, *args, **kwargs)
        if not ContextManager.get('currentRH', None):
            return func()
        ContextManager.setdefault('afterCommitQueue', []).append(func)

    return wrapper


def flush_after_commit_queue(execute):
    queue = ContextManager.get('afterCommitQueue', [])
    if execute:
        for func in queue:
            func()
    del queue[:]
