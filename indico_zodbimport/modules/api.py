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

from indico.core.db import db
from indico.modules.api import api_settings
from indico.util.console import cformat

from indico_zodbimport import Importer


class APIImporter(Importer):
    def migrate(self):
        self.migrate_settings()

    def migrate_settings(self):
        print cformat('%{white!}migrating settings')
        settings_map = {
            '_apiPersistentAllowed': 'allow_persistent',
            '_apiMode': 'security_mode',
            '_apiCacheTTL': 'cache_ttl',
            '_apiSignatureTTL': 'signature_ttl'
        }
        for old, new in settings_map.iteritems():
            api_settings.set(new, getattr(self.zodb_root['MaKaCInfo']['main'], old))
        db.session.commit()
