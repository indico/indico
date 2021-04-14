# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        return SideMenuItem('applications', _('Applications'), url_for('oauth.apps'), section='integration')


@signals.menu.items.connect_via('user-profile-sidemenu')
def _extend_profile_sidemenu(sender, user, **kwargs):
    yield SideMenuItem('applications', _('Applications'), url_for('oauth.user_profile'), 40, disabled=user.is_system)
