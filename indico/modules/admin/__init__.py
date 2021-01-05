# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.modules.admin.controllers.base import RHAdminBase
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuSection, TopMenuItem


__all__ = ('RHAdminBase',)


@signals.menu.sections.connect_via('admin-sidemenu')
def _sidemenu_sections(sender, **kwargs):
    yield SideMenuSection('security', _("Security"), 90, icon='shield')
    yield SideMenuSection('user_management', _("User Management"), 60, icon='users')
    yield SideMenuSection('customization', _("Customization"), 50, icon='wrench')
    yield SideMenuSection('integration', _("Integration"), 30, icon='earth')
    yield SideMenuSection('homepage', _("Homepage"), 40, icon='home')


@signals.menu.items.connect_via('top-menu')
def _topmenu_items(sender, **kwargs):
    if session.user and session.user.is_admin:
        yield TopMenuItem('admin', _('Administration'), url_for('core.admin_dashboard'), 70)
