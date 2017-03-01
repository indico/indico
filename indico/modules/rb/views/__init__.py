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

from indico.legacy.webinterface.pages.main import WPMainBase

from indico.util.i18n import _
from indico.web.menu import render_sidemenu


class WPRoomBookingBase(WPMainBase):

    def _getTitle(self):
        return '{} - {}'.format(WPMainBase._getTitle(self), _('Room Booking'))

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage(['Management', 'RoomBooking'])

    def _getSideMenu(self):
        return render_sidemenu('rb-sidemenu', active_item=self.sidemenu_option)

    def _isRoomBooking(self):
        return True
