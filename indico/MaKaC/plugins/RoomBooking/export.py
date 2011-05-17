# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2011 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import pytz
from indico.web.http_api import ExportInterface, LimitExceededException, Exporter
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api.responses import HTTPAPIError
from indico.web.wsgi import webinterface_handler_config as apache
from indico.util.fossilize import fossilize, IFossil
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.plugins.RoomBooking.default.factory import Factory
from MaKaC.rb_room import RoomBase
from MaKaC.rb_location import CrossLocationQueries
from MaKaC.fossils.roomBooking import IRoomFossil

globalExporters = ['RoomExporter']

class RoomExporter(Exporter):
    TYPES = ('room', )
    RE = r'(?P<location>\w+)/(?P<idlist>\w+(?:-\w+)*)'
    DEFAULT_DETAIL = 'rooms'
    MAX_RECORDS = {
        'rooms': 1000
    }

    def _getParams(self):
        super(RoomExporter, self)._getParams()
        self._location = self._urlParams['location']
        self._idList = self._urlParams['idlist'].split('-')

    def export_room(self, aw):
        expInt = RoomExportInterface(aw, self)
        return expInt.room(self._location, self._idList)

class IRoomMetadataFossil(IFossil):

    def id(self):
        pass
    def name(self):
        pass
    def locationName(self):
        pass
    def floor(self):
        pass
    def roomNr(self):
        pass
    def building(self):
        pass
    def getBookingUrl(self):
        pass
    def getFullName(self):
        pass

class RoomExportInterface(ExportInterface):
    DETAIL_INTERFACES = {
        'rooms': IRoomMetadataFossil
    }

    def room(self, location, idlist):
        Factory.getDALManager().connect()

        rooms = CrossLocationQueries.getRooms(location)

        def _iterate_rooms(objIds):
            objIds = map(int, objIds)
            return (room for room in rooms if room.id in objIds)

        it = self._process(_iterate_rooms(idlist))
        Factory.getDALManager().disconnect()
        return it