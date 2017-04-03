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
from indico.modules.core.settings import core_settings, social_settings

from indico_zodbimport import Importer, convert_to_unicode


class GlobalSettingsImporter(Importer):
    def migrate(self):
        self.migrate_settings()

    def migrate_settings(self):
        self.print_step('migrating global settings')
        minfo = self.zodb_root['MaKaCInfo']['main']
        core_settings.set_multi({
            'site_title': convert_to_unicode(minfo._title),
            'site_organization': convert_to_unicode(minfo._organisation),
        })
        social_settings.set_multi({
            'enabled': bool(minfo._socialAppConfig['active']),
            'facebook_app_id': convert_to_unicode(minfo._socialAppConfig['facebook']['appId'])
        })
        db.session.commit()
