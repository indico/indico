# -*- coding: utf-8 -*-
##
##
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

from MaKaC.plugins.RoomBooking.default.dalManager import DALManager
from MaKaC.plugins.RoomBooking.default.room import Room
from indico.core.db import DBMgr


def _main():
    print 'Month\tYear\tRoom'
    for room in Room.getRooms():
        print '{1:.3f}\t{2:.3f}\t{0}'.format(room.getFullName(),
                                             room.getMyAverageOccupation('pastmonth') * 100,
                                             room.getMyAverageOccupation('pastyear') * 100)


def main():
    with DBMgr.getInstance().global_connection():
        DALManager.connect()
        try:
            _main()
        finally:
            DALManager.disconnect()


if __name__ == '__main__':
    main()
