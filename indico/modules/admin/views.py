# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.util.i18n import _
from indico.web.breadcrumbs import render_breadcrumbs
from indico.web.flask.util import url_for
from indico.web.menu import get_menu_item
from indico.web.views import WPDecorated, WPJinjaMixin


class WPAdmin(WPJinjaMixin, WPDecorated):
    """Base class for admin pages."""

    def __init__(self, rh, active_menu_item=None, **kwargs):
        kwargs['active_menu_item'] = active_menu_item or self.sidemenu_option
        WPDecorated.__init__(self, rh, **kwargs)

    def _get_breadcrumbs(self):
        menu_item = get_menu_item('admin-sidemenu', self._kwargs['active_menu_item'])
        items = [(_('Administration'), url_for('core.admin_dashboard'))]
        if menu_item:
            items.append(menu_item.title)
        return render_breadcrumbs(*items)

    def _get_body(self, params):
        return self._get_page_content(params)
