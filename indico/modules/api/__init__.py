# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.core import signals
from indico.core.db import db
from indico.core.models.settings import SettingsProxy
from indico.modules.api.models.keys import APIKey


__all__ = ('settings',)


@signals.merge_users.connect
def _merge_users(user, merged, **kwargs):
    # Get the current active API keys
    ak_user = user.api_key
    ak_merged = merged.api_key
    # Move all inactive keys to the new user
    APIKey.find(user_id=int(merged.id), is_active=False).update({'user_id': int(user.id)})
    if ak_merged and not ak_user:
        ak_merged.user = user
    elif ak_user and ak_merged:
        # Both have a key, keep the main one unless it's unused and the merged one isn't.
        if ak_user.use_count or not ak_merged.use_count:
            ak_merged.is_active = False
            ak_merged.user = user
        else:
            ak_user.is_active = False
            db.session.flush()  # flush the deactivation so we can reassociate the user
            ak_merged.user = user


settings = SettingsProxy('api', {
    'require_https': False,
    'allow_persistent': False,
    'security_mode': 0,  # TODO: use an enum
    # TODO: check if api related messages really need to be configurable
    'cache_ttl': 600,
    'signature_ttl': 600
})
