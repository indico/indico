# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.core.settings import SettingsProxy
from indico.modules.api.models.keys import APIKey
from indico.util.i18n import _
from indico.util.struct.enum import IndicoEnum
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('settings',)


class APIMode(int, IndicoEnum):
    KEY = 0  # public requests without API key, authenticated requests with api key
    ONLYKEY = 1  # all requests require an API key
    SIGNED = 2  # public requests without API key, authenticated requests with api key and signature
    ONLYKEY_SIGNED = 3  # all requests require an API key, authenticated requests need signature
    ALL_SIGNED = 4  # all requests require an api key and a signature


api_settings = SettingsProxy('api', {
    'allow_persistent': False,
    'security_mode': APIMode.KEY.value,
    'cache_ttl': 600,
    'signature_ttl': 600
})


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    # Get the current active API keys
    ak_user = target.api_key
    ak_merged = source.api_key
    # Move all inactive keys to the new user
    APIKey.find(user_id=source.id, is_active=False).update({'user_id': target.id})
    if ak_merged and not ak_user:
        ak_merged.user = target
    elif ak_user and ak_merged:
        # Both have a key, keep the main one unless it's unused and the merged one isn't.
        if ak_user.use_count or not ak_merged.use_count:
            ak_merged.is_active = False
            ak_merged.user = target
        else:
            ak_user.is_active = False
            db.session.flush()  # flush the deactivation so we can reassociate the user
            ak_merged.user = target


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        return SideMenuItem('api', _("API"), url_for('api.admin_settings'), section='integration')


@signals.menu.items.connect_via('user-profile-sidemenu')
def _extend_profile_sidemenu(sender, **kwargs):
    yield SideMenuItem('api', _('HTTP API'), url_for('api.user_profile'), 30)
