# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.util.i18n import _
from indico.web.breadcrumbs import Breadcrumb, render_breadcrumbs
from indico.web.flask.util import url_for
from indico.web.menu import get_menu_item
from indico.web.views import WPDecorated, WPJinjaMixin


class WPAdmin(WPJinjaMixin, WPDecorated):
    """Base class for admin pages."""

    def __init__(self, rh, active_menu_item=None, **kwargs):
        self.active_menu_item = active_menu_item or self.sidemenu_option
        kwargs['active_menu_item'] = self.active_menu_item
        WPDecorated.__init__(self, rh, **kwargs)

    def _get_breadcrumbs(self):
        menu_item = get_menu_item('admin-sidemenu', self.active_menu_item)
        items = [Breadcrumb(_('Administration'), url_for('core.admin_dashboard'))]
        if menu_item:
            items.append(menu_item.title)
        return render_breadcrumbs(*items)

    def _get_body(self, params):
        return self._get_page_content(params)

    @property
    def _extra_title_parts(self):
        title_parts = super()._extra_title_parts
        if menu_item := get_menu_item('admin-sidemenu', self.active_menu_item):
            return (*title_parts, menu_item.title)
        return title_parts
