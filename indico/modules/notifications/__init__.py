# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.settings import SettingsProxy
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('notifications')

settings = SettingsProxy('notifications', {
    'webhook_url': '',
    'channel_id': '',
    'secret_token': ''
})


@signals.core.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.notifications.tasks  # noqa: F401


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        return SideMenuItem('notifications', 'Notifications', url_for('notifications.admin'), section='integration')
