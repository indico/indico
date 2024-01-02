# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from functools import wraps

from celery import current_task

from indico.core.cache import make_scoped_cache
from indico.core.logger import Logger


_lock_cache = make_scoped_cache('task-locks')


def locked_task(f):
    """Decorator to prevent a task from running multiple times at once."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        name = current_task.name
        if _lock_cache.get(name):
            Logger.get('celery').warning('Task %s is locked; not executing it. '
                                         'To manually unlock it, run `indico celery unlock %s`',
                                         name, name)
            return
        _lock_cache.set(name, True, 86400)
        try:
            return f(*args, **kwargs)
        finally:
            _lock_cache.delete(name)
    return wrapper


def unlock_task(name):
    """Unlock a locked task.

    :return: ``True`` if the task has been unlocked; ``False`` if it was not locked.
    """
    if not _lock_cache.get(name):
        return False
    _lock_cache.delete(name)
    return True
