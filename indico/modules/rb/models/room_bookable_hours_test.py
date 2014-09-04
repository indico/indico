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

from datetime import time

from indico.modules.rb.models.room_bookable_hours import BookableHours


pytest_plugins = 'indico.modules.rb.testing.fixtures'


def test_fits_period():
    bh = BookableHours(start_time=time(12), end_time=time(15))
    assert bh.fits_period(time(12), time(13))
    assert bh.fits_period(time(14), time(15))
    assert bh.fits_period(time(12), time(15))
    assert bh.fits_period(time(12, 30), time(14, 30))
    assert bh.fits_period(time(12), time(12))
    assert bh.fits_period(time(15), time(15))
    assert not bh.fits_period(time(0), time(12))
    assert not bh.fits_period(time(15), time(15, 1))
    assert not bh.fits_period(time(11), time(16))
