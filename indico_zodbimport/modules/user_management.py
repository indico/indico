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
from indico.modules.users import user_management_settings
from indico_zodbimport import Importer


class UserManagementImporter(Importer):
    """Migrate account-related settings"""

    def migrate(self):
        self._migrate_settings()

    def _migrate_settings(self):
        self.print_step('Migrating user management settings')
        settings_dict = {
            '_notifyAccountCreation': 'notify_account_creation'
        }

        for old_setting_name, new_setting_name in settings_dict.iteritems():
            user_management_settings.set(new_setting_name, getattr(self.zodb_root['MaKaCInfo']['main'],
                                         old_setting_name))
        db.session.commit()
