# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
from indico.modules.legal import legal_settings

from indico_zodbimport import Importer, convert_to_unicode


class LegalImporter(Importer):
    def migrate(self):
        self.migrate_settings()

    def migrate_settings(self):
        self.print_step('migrating settings')
        settings_map = {
            '_protectionDisclaimerProtected': 'protected_disclaimer',
            '_protectionDisclaimerRestricted': 'restricted_disclaimer'
        }
        for old, new in settings_map.iteritems():
            legal_settings.set(new, convert_to_unicode(getattr(self.zodb_root['MaKaCInfo']['main'], old)))
        db.session.commit()
