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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from zope.interface import implements, Interface

from indico.core.index import OOIndex, Index, Catalog
from indico.core.extpoint.base import Component
from indico.core.extpoint.reservation import IReservationListener, IReservationStartStopListener
from indico.core.extpoint.index import ICatalogIndexProvider

from MaKaC.user import GroupHolder
from MaKaC.rb_location import IIndexableByManagerIds
from MaKaC.plugins.RoomBooking.common import getRoomBookingOption
from MaKaC.plugins.RoomBooking.notifications import sendReservationStartStopNotification
from MaKaC.rb_location import CrossLocationQueries


class RoomManagerIndex(OOIndex):

    def __init__(self):
        super(RoomManagerIndex, self).__init__(IIndexableByManagerIds)

    def initialize(self, dbi=None):
        # empty tree
        self.clear()

        for room in set(CrossLocationQueries.getRooms()):
            self.index_obj(room.guid)


class CatalogIndexProvider(Component):
    implements(ICatalogIndexProvider)

    def catalogIndexProvider(self, obj):
        return [('user_room', RoomManagerIndex)]
