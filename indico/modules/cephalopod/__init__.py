# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.settings import SettingsProxy
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('logger', 'cephalopod_settings')

logger = Logger.get('cephalopod')

cephalopod_settings = SettingsProxy('cephalopod', {
    'show_migration_message': False,
    'joined': False,
    'contact_email': None,
    'contact_name': None,
    'uuid': None
})


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        return SideMenuItem('cephalopod', _("Community Hub"), url_for('cephalopod.index'), section='integration')
