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

from datetime import datetime, time

import pytest

from indico.modules.rb.models.room_bookable_hours import BookableHours


@pytest.mark.parametrize(('start_time', 'end_time', 'expected'), (
    ('12:00', '13:00', True),
    ('14:00', '15:00', True),
    ('12:00', '15:00', True),
    ('12:30', '14:30', True),
    ('12:00', '12:00', True),
    ('15:00', '15:00', True),
    ('15:00', '15:01', False),
    ('00:00', '12:00', False),
    ('11:00', '16:00', False),
    ('14:00', '16:00', False),
))
def test_fits_period(start_time, end_time, expected):
    start_time = datetime.strptime(start_time, '%H:%M').time()
    end_time = datetime.strptime(end_time, '%H:%M').time()
    bh = BookableHours(start_time=time(12), end_time=time(15))
    assert bh.fits_period(start_time, end_time) == expected
