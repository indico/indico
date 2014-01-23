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

from indico.core.db import DBMgr
from MaKaC.rb_factory import Factory
from MaKaC.rb_location import CrossLocationQueries

DBMgr.getInstance().startRequest()
Factory.getDALManager().connect()

idontknow = "I don't know"

rooms = CrossLocationQueries.getRooms( allFast = True )
for room in rooms:
    print "[%s][%s] %s"%(room.id, room.needsAVCSetup,room.getAvailableVC())
    if room.needsAVCSetup:
        if not idontknow in room.getAvailableVC():
            room.avaibleVC.append(idontknow)
            room.update()


Factory.getDALManager().commit()
Factory.getDALManager().disconnect()
DBMgr.getInstance().endRequest()



DBMgr.getInstance().startRequest()
Factory.getDALManager().connect()

rooms = CrossLocationQueries.getRooms( allFast = True )
for room in rooms:
    print "[%s][%s] %s"%(room.id, room.needsAVCSetup,room.getAvailableVC())


Factory.getDALManager().disconnect()
DBMgr.getInstance().endRequest()
