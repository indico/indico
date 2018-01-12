# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.views import WPConferenceDisplayBase
from indico.util.i18n import _
from indico.web.breadcrumbs import render_breadcrumbs
from indico.web.views import WPDecorated, WPJinjaMixin


class WPVCManageEvent(WPEventManagement):
    sidemenu_option = 'videoconference'
    template_prefix = 'vc/'

    def getCSSFiles(self):
        return WPEventManagement.getCSSFiles(self) + self._asset_env['selectize_css'].urls()

    def getJSFiles(self):
        return (WPEventManagement.getJSFiles(self) +
                self._asset_env['modules_vc_js'].urls() +
                self._asset_env['selectize_js'].urls())


class WPVCEventPage(WPConferenceDisplayBase):
    menu_entry_name = 'videoconference_rooms'
    template_prefix = 'vc/'

    def getJSFiles(self):
        return WPConferenceDisplayBase.getJSFiles(self) + self._asset_env['modules_vc_js'].urls()


class WPVCService(WPJinjaMixin, WPDecorated):
    template_prefix = 'vc/'

    def _get_breadcrumbs(self):
        return render_breadcrumbs(_('Videoconference'))

    def _getBody(self, params):
        return self._getPageContent(params)
