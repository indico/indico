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

import inspect
from datetime import datetime

import freezegun
import pytest
from sqlalchemy import cast, DateTime
from sqlalchemy.sql.functions import _FunctionGenerator


@pytest.fixture
def monkeypatch_methods(monkeypatch):
    """Monkeypatches all methods from `cls` onto `target`

    This utility lets you easily mock multiple methods in an existing class.
    In case of classmethods the binding will not be changed, i.e. `cls` will
    keep pointing to the source class and not the target class.
    """

    def _monkeypatch_methods(target, cls):
        for name, method in inspect.getmembers(cls, inspect.ismethod):
            if method.im_self is None:
                # For unbound methods we need to copy the underlying function
                method = method.im_func
            monkeypatch.setattr('{}.{}'.format(target, name), method)

    return _monkeypatch_methods


@pytest.yield_fixture
def freeze_time(monkeypatch):
    """Returns a function that freezes the current time

    It affects datetime.now, date.today, etc. and also SQLAlchemy's `func.now()`
    which simply returns the current time from `datetime.now()` instead of
    retrieving it using the actual `now()` function of PostgreSQL.
    """
    freezer = [None]
    orig_call = _FunctionGenerator.__call__

    def FunctionGenerator_call(self, *args, **kwargs):
        if self._FunctionGenerator__names == ['now']:
            return cast(datetime.now().isoformat(), DateTime)
        return orig_call(self, *args, **kwargs)

    monkeypatch.setattr(_FunctionGenerator, '__call__', FunctionGenerator_call)

    def _freeze_time(time_to_freeze):
        freezer[0] = freezegun.freeze_time(time_to_freeze)
        freezer[0].start()

    yield _freeze_time
    if freezer[0]:
        freezer[0].stop()
