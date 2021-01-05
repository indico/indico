# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem, TopMenuItem, TopMenuSection
from indico.web.util import url_for_index


@signals.menu.sections.connect_via('top-menu')
def _topmenu_sections(sender, **kwargs):
    yield TopMenuSection('services', _('Services'), 60)
    yield TopMenuSection('help', _('Help'), -10)  # put the help section always last


@signals.menu.items.connect_via('top-menu')
def _topmenu_items(sender, **kwargs):
    yield TopMenuItem('home', _('Home'), url_for_index(), 100)


@signals.menu.items.connect_via('admin-sidemenu')
def _sidemenu_items(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('settings', _('General Settings'), url_for('core.settings'), 100, icon='settings')
