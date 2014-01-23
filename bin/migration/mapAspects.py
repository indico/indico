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
from MaKaC.rb_location import Location, MapAspect
from MaKaC.plugins.RoomBooking.default.factory import Factory

aspects = [
    {'id': 0, 'name':'Meyrin', 'centerLatitude': 46.23456689405093, 'centerLongitude': 6.046686172485352, 'topLeftLatitude': '46.225660710473136', 'topLeftLongitude': '6.030035018920898', 'bottomRightLatitude': '46.2434716324829', 'bottomRightLongitude': '6.063294410705566', 'zoomLevel':15, 'defaultOnStartup': True},
    {'id': 1, 'name':'PREVESSIN', 'centerLatitude': 46.259051447415175, 'centerLongitude': 6.057773351931246, 'topLeftLatitude': '46.2501492379416', 'topLeftLongitude': '6.041107177734375', 'bottomRightLatitude': '46.26795221179669', 'bottomRightLongitude': '6.074366569519043', 'zoomLevel':15, 'defaultOnStartup': False},
    {'id': 2, 'name':'POINT 1', 'centerLatitude': 46.23573201283012, 'centerLongitude': 6.054509639707248, 'topLeftLatitude': '46.23350564968721', 'topLeftLongitude': '6.050344705581665', 'bottomRightLatitude': '46.23795828565159', 'bottomRightLongitude': '6.058659553527832', 'zoomLevel':17, 'defaultOnStartup': False},
    {'id': 3, 'name':'POINT 2', 'centerLatitude': 46.25115822762375, 'centerLongitude': 6.020456314054172, 'topLeftLatitude': '46.24893249040227', 'topLeftLongitude': '6.016291379928589', 'bottomRightLatitude': '46.253383874525866', 'bottomRightLongitude': '6.024606227874756', 'zoomLevel':17, 'defaultOnStartup': False},
    {'id': 4, 'name':'POINT 5', 'centerLatitude': 46.30958858268458, 'centerLongitude': 6.077267646724067, 'topLeftLatitude': '46.30736521774798', 'topLeftLongitude': '6.073100566864014', 'bottomRightLatitude': '46.31181185731005', 'bottomRightLongitude': '6.081415414810181', 'zoomLevel':17, 'defaultOnStartup': False},
    {'id': 5, 'name':'POINT 6', 'centerLatitude': 46.29345231426436, 'centerLongitude': 6.1115119456917455, 'topLeftLatitude': '46.29122829396059', 'topLeftLongitude': '6.107347011566162', 'bottomRightLatitude': '46.295676244254715', 'bottomRightLongitude': '6.115661859512329', 'zoomLevel':17, 'defaultOnStartup': False},
    {'id': 6, 'name':'POINT 8', 'centerLatitude': 46.24158691675184, 'centerLongitude': 6.097038745847385, 'topLeftLatitude': '46.2393607911537', 'topLeftLongitude': '6.092873811721802', 'bottomRightLatitude': '46.24381295202931', 'bottomRightLongitude': '6.101188659667969', 'zoomLevel':17, 'defaultOnStartup': False},
]

DBMgr.getInstance().startRequest()
Factory.getDALManager().connect()

location = Location.parse('CERN')

for aspectData in aspects:
    aspect = MapAspect()
    aspect.updateFromDictionary(aspectData)
    location.addAspect(aspect)

DBMgr.getInstance().endRequest()
