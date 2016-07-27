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

from __future__ import unicode_literals

from MaKaC.webinterface.pages.admins import WPAdminsBase
from MaKaC.webinterface.pages.base import WPJinjaMixin
from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase, WPConferenceModifBase


class WPPaymentJinjaMixin(WPJinjaMixin):
    template_prefix = 'events/payment/'


class WPPaymentAdmin(WPPaymentJinjaMixin, WPAdminsBase):
    sidemenu_option = 'payment'


class WPPaymentEventManagement(WPConferenceModifBase, WPPaymentJinjaMixin):
    template_prefix = 'events/payment/'
    sidemenu_option = 'payment'

    def _getPageContent(self, params):
        return WPPaymentJinjaMixin._getPageContent(self, params)


class WPPaymentEvent(WPConferenceDefaultDisplayBase, WPPaymentJinjaMixin):
    menu_entry_name = 'registration'

    def _getBody(self, params):
        return WPPaymentJinjaMixin._getPageContent(self, params)
