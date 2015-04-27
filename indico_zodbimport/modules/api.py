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

from datetime import timedelta
from uuid import uuid4

import pytz
from babel.dates import get_timezone

from indico.core.db import db
from indico.modules.api import settings as api_settings
from indico.modules.api.models.keys import APIKey
from indico.util.console import cformat
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode


class APIImporter(Importer):
    def has_data(self):
        return bool(APIKey.find().count())

    def migrate(self):
        self.migrate_settings()
        self.migrate_keys()

    def migrate_settings(self):
        print cformat('%{white!}migrating settings')
        settings_map = {
            '_apiHTTPSRequired': 'require_https',
            '_apiPersistentAllowed': 'allow_persistent',
            '_apiMode': 'security_mode',
            '_apiCacheTTL': 'cache_ttl',
            '_apiSignatureTTL': 'signature_ttl'
        }
        for old, new in settings_map.iteritems():
            api_settings.set(new, getattr(self.zodb_root['MaKaCInfo']['main'], old))

    def migrate_keys(self):
        print cformat('%{white!}migrating api keys')
        for idx_key, ak in committing_iterator(self.zodb_root['apikeys'].iteritems()):
            if idx_key != ak._key:
                print cformat('%{red!}!!!%{reset} '
                              '%{yellow!}Skipping {} - index key {} does not match').format(ak._key, idx_key)
                continue
            elif str(ak._user.id) not in self.zodb_root['avatars']:
                print cformat('%{red!}!!!%{reset} '
                              '%{yellow!}Skipping {} - user {} does not exist').format(ak._key, ak._user.id)
                continue
            elif ak._user.apiKey != ak:
                print cformat('%{red!}!!!%{reset} '
                              '%{yellow!}Skipping {} - user {} has a different api key set').format(ak._key,
                                                                                                    ak._user.id)
                continue

            last_used_uri = None
            if ak._lastPath and ak._lastQuery:
                last_used_uri = '{}?{}'.format(convert_to_unicode(ak._lastPath), convert_to_unicode(ak._lastQuery))
            elif ak._lastPath:
                last_used_uri = convert_to_unicode(ak._lastPath)

            api_key = APIKey(token=ak._key, secret=ak._signKey, user_id=ak._user.id, is_blocked=ak._isBlocked,
                             is_persistent_allowed=getattr(ak, '_persistentAllowed', False),
                             created_dt=self._to_utc(ak._createdDT), last_used_dt=self._to_utc(ak._lastUsedDT),
                             last_used_ip=ak._lastUsedIP, last_used_uri=last_used_uri,
                             last_used_auth=ak._lastUseAuthenticated, use_count=ak._useCount)
            db.session.add(api_key)
            print cformat('%{green}+++%{reset} %{cyan}{}%{reset} [%{blue!}{}%{reset}]').format(ak._key, ak._user.email)

            for old_key in ak._oldKeys:
                # We have no creation time so we use *something* older..
                fake_created_dt = self._to_utc(ak._createdDT) - timedelta(hours=1)
                # We don't have anything besides the api key for old keys, so we use a random secret
                old_api_key = APIKey(token=old_key, secret=unicode(uuid4()), user_id=ak._user.id,
                                     created_dt=fake_created_dt, is_active=False)
                db.session.add(old_api_key)
                print cformat('%{blue!}***%{reset} %{cyan}{}%{reset} [%{yellow}old%{reset}]').format(old_key)

            db.session.flush()

    def _to_utc(self, dt):
        if dt is None:
            return None
        server_tz = get_timezone(getattr(self.zodb_root['MaKaCInfo']['main'], '_timezone', 'UTC'))
        return server_tz.localize(dt).astimezone(pytz.utc)
