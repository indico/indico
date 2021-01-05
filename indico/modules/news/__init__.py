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


logger = Logger.get('news')

news_settings = SettingsProxy('news', {
    # Whether to show the recent news on the home page
    'show_recent': True,
    # The number of recent news to show on the home page
    'max_entries': 3,
    # How old a news may be to be shown on the home page
    'max_age': 0,
    # How long a news is labelled as 'new'
    'new_days': 14
})


@signals.menu.items.connect_via('admin-sidemenu')
def _sidemenu_items(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('news', _('News'), url_for('news.manage'), section='homepage')
