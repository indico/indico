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

from datetime import datetime

from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod


pytest_plugins = 'indico.modules.rb.testing.fixtures'


def test_overlaps():
    nbp = NonBookablePeriod(start_dt=datetime(2014, 12, 5), end_dt=datetime(2014, 12, 6))
    assert nbp.overlaps(datetime(2014, 12, 4), datetime(2014, 12, 6))
    assert nbp.overlaps(datetime(2014, 12, 5, 0, 1), datetime(2014, 12, 5, 0, 1))
    assert not nbp.overlaps(datetime(2014, 12, 5), datetime(2014, 12, 5))
    assert not nbp.overlaps(datetime(2014, 12, 1), datetime(2014, 12, 5))
    assert not nbp.overlaps(datetime(2014, 12, 6), datetime(2014, 12, 7))
