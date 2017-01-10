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

from datetime import datetime

import pytest

from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod


@pytest.mark.parametrize(('start_dt', 'end_dt', 'expected'), (
    ('2014-12-04 00:00', '2014-12-06 00:00', True),
    ('2014-12-05 00:01', '2014-12-05 00:01', True),
    ('2014-12-05 00:00', '2014-12-05 00:00', False),
    ('2014-12-01 00:00', '2014-12-05 00:00', False),
    ('2014-12-06 00:00', '2014-12-07 00:00', False),
))
def test_overlaps(start_dt, end_dt, expected):
    start_dt = datetime.strptime(start_dt, '%Y-%m-%d %H:%M')
    end_dt = datetime.strptime(end_dt, '%Y-%m-%d %H:%M')
    nbp = NonBookablePeriod(start_dt=datetime(2014, 12, 5), end_dt=datetime(2014, 12, 6))
    assert nbp.overlaps(start_dt, end_dt) == expected
