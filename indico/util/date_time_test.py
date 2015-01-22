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
from dateutil.parser import parse

from indico.util.date_time import round_up_month


@pytest.mark.parametrize(('current_date', 'from_day', 'expected_month'), (
    ('2014-10-01', None, 11),
    ('2014-10-01', 1,    11),
    ('2014-10-01', 2,    10),
))
def test_round_up_month(current_date, from_day, expected_month):
    assert round_up_month(parse(current_date), from_day=from_day).month == expected_month
