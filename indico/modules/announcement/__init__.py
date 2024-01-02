# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.core.settings import SettingsProxy
from indico.util.i18n import _
from indico.util.string import render_markdown
from indico.web.flask.templating import template_hook
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


announcement_settings = SettingsProxy('announcement', {
    'enabled': False,
    'message': ''
})


@template_hook('global-announcement', markup=False)
def _inject_announcement_header(**kwargs):
    if not announcement_settings.get('enabled'):
        return
    if message := announcement_settings.get('message'):
        return ('warning', render_markdown(message, extra_html=True))


@signals.menu.items.connect_via('admin-sidemenu')
def _sidemenu_items(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('announcement', _('Announcement'), url_for('announcement.manage'), section='homepage')
