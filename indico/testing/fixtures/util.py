# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import inspect
from datetime import datetime

import freezegun
import pytest
from sqlalchemy import DateTime, cast
from sqlalchemy.sql.functions import _FunctionGenerator


@pytest.fixture
def monkeypatch_methods(monkeypatch):
    """Monkeypatch all methods from `cls` onto `target`.

    This utility lets you easily mock multiple methods in an existing class.
    In case of classmethods the binding will not be changed, i.e. `cls` will
    keep pointing to the source class and not the target class.
    """

    def _monkeypatch_methods(target, cls):
        for name, method in inspect.getmembers(cls, inspect.ismethod):
            if method.__self__ is None:
                # For unbound methods we need to copy the underlying function
                method = method.__func__
            monkeypatch.setattr('{}.{}'.format(target, name), method)

    return _monkeypatch_methods


@pytest.fixture
def freeze_time(monkeypatch):
    """Return a function that freezes the current time.

    It affects datetime.now, date.today, etc. and also SQLAlchemy's `func.now()`
    which simply returns the current time from `datetime.now()` instead of
    retrieving it using the actual `now()` function of PostgreSQL.
    """
    freezers = []
    orig_call = _FunctionGenerator.__call__

    def FunctionGenerator_call(self, *args, **kwargs):
        if self._FunctionGenerator__names == ['now']:
            return cast(datetime.now().isoformat(), DateTime)
        return orig_call(self, *args, **kwargs)

    monkeypatch.setattr(_FunctionGenerator, '__call__', FunctionGenerator_call)

    def _freeze_time(time_to_freeze):
        freezer = freezegun.freeze_time(time_to_freeze)
        freezer.start()
        freezers.append(freezer)

    yield _freeze_time
    for freezer in reversed(freezers):
        freezer.stop()
