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

from indico.modules.rb.views.admin import WPRoomBookingAdminBase
from MaKaC.webinterface.wcomponents import WTemplated


class WPRoomBookingRoomForm(WPRoomBookingAdminBase):
    _userData = ['favorite-user-list']

    def _setActiveTab(self):
        WPRoomBookingAdminBase._setActiveTab(self)
        self._subTabConfig.setActive()

    def _getTabContent(self, params):
        return WTemplated('RoomBookingRoomForm').getHTML(params)
