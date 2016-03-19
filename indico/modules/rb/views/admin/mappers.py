# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from indico.core.config import Config
from indico.modules.rb.views.admin import WPRoomsBase
from MaKaC.roomMapping import RoomMapperHolder
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.wcomponents import WTemplated


class WPRoomMapperBase(WPRoomsBase):
    def _setActiveTab(self):
        self._subTabRoomMappers.setActive()


class WPRoomMapperList(WPRoomMapperBase):
    def __init__(self, rh, params):
        WPRoomMapperBase.__init__(self, rh)
        self._params = params

    def _getTabContent(self, params):
        criteria = {}
        if filter(lambda x: self._params[x], self._params):
            criteria['name'] = self._params.get('sName', '')
        return WRoomMapperList(criteria).getHTML()


class WRoomMapperList(WTemplated):
    def __init__(self, criteria):
        self._criteria = criteria

    def _performSearch(self, criteria):
        return RoomMapperHolder().match(criteria)

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars['createRoomMapperURL'] = urlHandlers.UHNewRoomMapper.getURL()
        wvars['searchRoomMappersURL'] = urlHandlers.UHRoomMappers.getURL()
        wvars['roomMappers'] = self._performSearch(self._criteria) if self._criteria else []
        return wvars


class WPRoomMapperDetails(WPRoomMapperBase):
    def __init__(self, rh, roomMapper):
        WPRoomMapperBase.__init__(self, rh)
        self._roomMapper = roomMapper

    def _getTabContent(self, params):
        return WRoomMapperDetails(self._roomMapper).getHTML({
            'modifyURL': urlHandlers.UHRoomMapperModification.getURL(self._roomMapper)
        })


class WRoomMapperDetails(WTemplated):
    def __init__(self, rm):
        WTemplated.__init__(self)
        self._roomMapper = rm

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars['name'] = self._roomMapper.getName()
        wvars['description'] = self._roomMapper.getDescription()
        wvars['url'] = self._roomMapper.getBaseMapURL()
        wvars['placeName'] = self._roomMapper.getPlaceName()
        wvars['regexps'] = self._roomMapper.getRegularExpressions()
        return wvars


class WPRoomMapperCreation(WPRoomMapperBase):
    def _getTabContent(self, params):
        return WRoomMapperEdit().getHTML({
            'postURL': urlHandlers.UHRoomMapperPerformCreation.getURL()
        })


class WPRoomMapperModification(WPRoomMapperBase):
    def __init__(self, rh, domain):
        WPRoomMapperBase.__init__(self, rh)
        self._domain = domain

    def _getTabContent(self, params):
        return WRoomMapperEdit(self._domain).getHTML({
            'postURL': urlHandlers.UHRoomMapperPerformModification.getURL(self._domain)
        })


class WRoomMapperEdit(WTemplated):
    def __init__(self, rm=None):
        self._roomMapper = rm

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars['name'] = wvars['description'] = wvars['url'] = \
            wvars['placeName'] = wvars['regexps'] = wvars['locator'] = ''
        wvars['is_rb_active'] = Config.getInstance().getIsRoomBookingActive()
        if self._roomMapper:
            wvars['name'] = self._roomMapper.getName()
            wvars['description'] = self._roomMapper.getDescription()
            wvars['url'] = self._roomMapper.getBaseMapURL()
            wvars['placeName'] = self._roomMapper.getPlaceName()
            wvars['regexps'] = '\r\n'.join(self._roomMapper.getRegularExpressions())
            wvars['locator'] = self._roomMapper.getLocator().getWebForm()
        return wvars
