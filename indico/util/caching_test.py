# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
import pytest

from indico.util.caching import memoize_request


@pytest.fixture
def not_testing(app_context):
    app_context.config['TESTING'] = False
    try:
        yield
    finally:
        app_context.config['TESTING'] = True


@pytest.mark.usefixtures('request_context', 'not_testing')
def test_memoize_request_args():
    calls = [0]

    @memoize_request
    def fn(a, b, c='default', **kw):
        calls[0] += 1

    assert calls[0] == 0
    fn(1, 2)
    assert calls[0] == 1
    fn(1, 2)  # normal memoized call
    assert calls[0] == 1
    # default value explicitly provided (both as arg and kwarg)
    fn(1, 2, 'default')
    fn(1, 2, c='default')
    fn(1, b=2)
    fn(a=1, b=2, c='default')
    assert calls[0] == 1
    fn(2, 2, c='default')
    assert calls[0] == 2
    fn(2, 2)
    assert calls[0] == 2
    fn(2, 2, foo='bar')
    assert calls[0] == 3
    fn(a=2, b=2, foo='bar')
    assert calls[0] == 3


@pytest.mark.usefixtures('request_context', 'not_testing')
def test_memoize_request_legacy_class():
    # Make sure we don't choke on classes in the argument list,
    # e.g. when we have a classmethod on a legacy class
    calls = []

    @memoize_request
    def fn(a):
        calls.append(a)

    class Old():
        def getId(self):
            return 1

    class New(object):
        def getId(self):
            return 1

    old_instance = Old()
    new_instance = New()
    for i in range(2):
        fn(Old)
        fn(old_instance)
        fn(New)
        fn(new_instance)
    assert calls == [Old, old_instance, New, new_instance]
