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


class WPRoomBookingSettings(WPRoomBookingAdminBase):
    def _setActiveTab(self):
        WPRoomBookingAdminBase._setActiveTab(self)
        self._subTabMain.setActive()

    def _getTabContent(self, params):
        params['field_opts'] = {
            'assistance_emails': {'rows': 3, 'cols': 40},
            'notification_hour': {'size': 2},
            'notification_before_days': {'size': 2},
            'vc_support_emails': {'rows': 3, 'cols': 40}
        }
        return WTemplated('RoomBookingSettings').getHTML(params)
