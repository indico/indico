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

import inspect

import pytest


@pytest.fixture
def monkeypatch_methods(monkeypatch):
    """Monkeypatches all methods from `cls` onto `target`

    This utility lets you eaasily mock multiple methods in an existing class.
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


@pytest.fixture(params=(True, False))
def bool_flag(request):
    """Parametrizes the test with a boolean value that is once true and once false"""
    return request.param
