# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.modules.users import User


def test_full_name():
    assert User(first_name='Guinea', last_name='Pig').full_name == 'Guinea Pig'


@pytest.mark.parametrize(('last_name_first', 'last_name_upper', 'abbrev_first_name', 'expected'), (
    (False, False, False, 'Guinea Pig'),
    (False, False, True,  'G. Pig'),
    (False, True,  False, 'Guinea PIG'),
    (False, True,  True,  'G. PIG'),
    (True,  False, False, 'Pig, Guinea'),
    (True,  False, True,  'Pig, G.'),
    (True,  True,  False, 'PIG, Guinea'),
    (True,  True,  True,  'PIG, G.'),
))
def test_get_full_name(last_name_first, last_name_upper, abbrev_first_name, expected):
    u = User(first_name='Guinea', last_name='Pig')
    name = u.get_full_name(last_name_first=last_name_first, last_name_upper=last_name_upper,
                           abbrev_first_name=abbrev_first_name)
    assert name == expected
