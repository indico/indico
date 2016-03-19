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

import pytest
from enum import Enum

from indico.core.settings.models.settings import Setting


@pytest.mark.usefixtures('db')
def test_set_enum():
    class Useless(int, Enum):
        thing = 1337

    Setting.set_multi('foo', {'foo': Useless.thing})
    Setting.set('foo', 'bar', Useless.thing)
    for key in {'foo', 'bar'}:
        value = Setting.get('foo', key)
        assert value == Useless.thing
        assert value == Useless.thing.value
        assert not isinstance(value, Useless)  # we store it as a plain value!
