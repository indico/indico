# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.modules.groups.core import GroupProxy
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('GroupProxy',)


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        return SideMenuItem('groups', _("Groups"), url_for('groups.groups'), section='user_management')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    target.local_groups |= source.local_groups
    source.local_groups.clear()
