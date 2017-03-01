# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from functools import wraps

from celery import current_task

from indico.core.logger import Logger
from indico.legacy.common.cache import GenericCache


def locked_task(f):
    """Decorator to prevent a task from running multiple times at once."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        cache = GenericCache('task-locks')
        name = current_task.name
        if cache.get(name):
            Logger.get('celery').warning('Task {} is locked; not executing it'.format(name))
            return
        cache.set(name, True)
        try:
            return f(*args, **kwargs)
        finally:
            cache.delete(name)
    return wrapper
