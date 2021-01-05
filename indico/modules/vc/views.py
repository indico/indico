# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.views import WPConferenceDisplayBase
from indico.util.i18n import _
from indico.web.breadcrumbs import render_breadcrumbs
from indico.web.views import WPDecorated, WPJinjaMixin


class WPVCManageEvent(WPEventManagement):
    sidemenu_option = 'videoconference'
    template_prefix = 'vc/'
    bundles = ('module_vc.js', 'module_vc.css')


class WPVCEventPage(WPConferenceDisplayBase):
    menu_entry_name = 'videoconference_rooms'
    template_prefix = 'vc/'
    bundles = ('module_vc.js', 'module_vc.css')


class WPVCService(WPJinjaMixin, WPDecorated):
    template_prefix = 'vc/'

    def _get_breadcrumbs(self):
        return render_breadcrumbs(_('Videoconference'))

    def _get_body(self, params):
        return self._get_page_content(params)
