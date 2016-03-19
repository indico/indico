# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

from contextlib import contextmanager
from functools import partial, wraps

import transaction
from sqlalchemy.exc import IntegrityError
from ZODB.POSException import ConflictError

from indico.core.db import DBMgr
from indico.util.contextManager import ContextManager
from indico.util.decorators import smart_decorator


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


@contextmanager
def retry_request_on_conflict():
    """Converts an SQLIntegrityError to a conflict error (which triggers a retry)"""
    try:
        yield
    except IntegrityError as e:
        if 'duplicate key value violates' not in str(e):
            raise
        raise ConflictError(str(e))


@smart_decorator
def with_zodb(fn, commit=True):
    """Runs a function within a ZODB connection/transaction

    :param commit: if the transaction should be committed
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with DBMgr.getInstance().global_connection():
            try:
                result = fn(*args, **kwargs)
            except:
                transaction.abort()
                raise
            else:
                if commit:
                    transaction.commit()
                else:
                    transaction.abort()
            return result

    return wrapper
