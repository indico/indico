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

import warnings

from indico.core.config import config
from indico.util.string import return_ascii


def warn_on_access(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if config.DEBUG:
            warnings.warn('Called {}'.format(fn.__name__), stacklevel=2)
        return fn(*args, **kwargs)

    return wrapper


class LegacyConference(object):
    def __init__(self, event):
        self.event = event

    @return_ascii
    def __repr__(self):
        return '<Conference: {}>'.format(self.event)

    @property
    def id(self):
        return self.event.id

    @property
    def as_event(self):
        return self.event

    @warn_on_access
    def getId(self):
        return self.id

    @property
    @warn_on_access
    def locator(self):
        warnings.warn('Accessed Conference.locator', stacklevel=4)
        return self.event.locator
