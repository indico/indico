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

import os
import sys
from itertools import chain

from indico.core.config import Config
from indico.core.db import db
from indico.modules.events.static.models.static import StaticSite, StaticSiteState
from indico.modules.users import User
from indico.util.console import cformat
from indico.util.string import is_legacy_id
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer

STATE_MAPPING = {'Queued': StaticSiteState.failed,
                 'Generated': StaticSiteState.success,
                 'Failed': StaticSiteState.failed,
                 'Expired': StaticSiteState.expired}


class StaticSitesImporter(Importer):
    def has_data(self):
        return StaticSite.query.has_rows()

    def migrate(self):
        print cformat('%{white!}migrating static sites')
        for item in committing_iterator(chain.from_iterable(
                                        self.zodb_root['modules']['offlineEvents']._idxConf.itervalues())):

            event_id = item.conference.id
            if is_legacy_id(event_id):
                print cformat('%{red!}!!!%{reset} '
                              '%{white!}{0:6s}%{reset} %{yellow!}Event has non-numeric/broken ID').format(event_id)
                continue

            if event_id not in self.zodb_root['conferences']:
                print cformat('%{red!}!!!%{reset} '
                              '%{white!}{0:6s}%{reset} %{yellow!}Event deleted, skipping static site').format(event_id)
                continue

            event_id = int(event_id)
            user = self._get_user(item.avatar.id)
            state = STATE_MAPPING[item.status]
            requested_dt = item.requestTime
            file_name, file_path = self._get_file_data(item.file)

            if file_path is None and state == StaticSiteState.success:
                print cformat('%{yellow!}!!!%{reset} %{white!}{0:6d}%{reset} '
                              '%{yellow!}file missing, marking static site as expired.').format(event_id)
                state = StaticSite.expired

            static_site = StaticSite(creator=user, event_id=event_id, state=state, requested_dt=requested_dt)
            if static_site.state == StaticSiteState.success:
                static_site.path = file_path
            db.session.add(static_site)

            print cformat('%{green}+++%{reset} %{white!}{0.event_id:6d}%{reset} '
                          '%{cyan}{0}%{reset}').format(static_site)

    def _get_file_data(self, f):
        # this is based pretty much on MaterialLocalRepository.__getFilePath, but we don't
        # call any legacy methods in ZODB migrations to avoid breakage in the future.
        if f is None:
            return None, None

        # TODO: add a CLI parameter instead of getting legacy option from config
        archive_path = Config.getInstance().getArchiveDir()
        archive_id = f._LocalFile__archivedId
        repo = f._LocalFile__repository
        path = os.path.join(archive_path, repo._MaterialLocalRepository__files[archive_id])
        if os.path.exists(path):
            return f.fileName, path
        for mode, enc in (('strict', 'iso-8859-1'), ('replace', sys.getfilesystemencoding()), ('replace', 'ascii')):
            enc_path = path.decode('utf-8', mode).encode(enc, 'replace')
            if os.path.exists(enc_path):
                return f.fileName, enc_path
        return f.fileName, None

    def _get_user(self, user_id):
        user = User.get(user_id) or int(User.get(Config.getInstance().getJanitorUserId()))
        while user.merged_into_id is not None:
            user = user.merged_into_user
        return user
