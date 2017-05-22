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

from indico.legacy.webinterface.wcomponents import WTemplated
from indico.modules.rb.views.admin import WPRoomBookingAdminBase
from indico.util.i18n import _


class WPRoomBookingSettings(WPRoomBookingAdminBase):
    subtitle = _(u'Settings')

    def _get_legacy_content(self, params):
        params['field_opts'] = {
            'assistance_emails': {'rows': 3, 'cols': 40},
            'notification_before_days': {'size': 2},
            'notification_before_days_weekly': {'size': 2},
            'notification_before_days_monthly': {'size': 2},
            'vc_support_emails': {'rows': 3, 'cols': 40},
            'booking_limit': {'size': 3},
        }
        return WTemplated('RoomBookingSettings').getHTML(params)
