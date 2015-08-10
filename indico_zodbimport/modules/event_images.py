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

import mimetypes

import pytz
from babel.dates import get_timezone

from indico.core.db import db
from indico.modules.events.models.events import Event
from indico.modules.events.layout.models.images import ImageFile
from indico.modules.events.layout.models.legacy_mapping import LegacyImageMapping
from indico.util.console import cformat
from indico.util.date_time import now_utc
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer
from indico_zodbimport.util import LocalFileImporterMixin


class EventImageImporter(LocalFileImporterMixin, Importer):
    def __init__(self, **kwargs):
        kwargs = super(EventImageImporter, self)._set_config_options(**kwargs)
        super(EventImageImporter, self).__init__(**kwargs)

    def has_data(self):
        return bool(ImageFile.query.count())

    def migrate(self):
        self.migrate_event_images()

    def migrate_event_images(self):
        self.print_step('migrating event images')
        for event, picture in committing_iterator(self._iter_pictures()):
            local_file = picture._localFile
            content_type = mimetypes.guess_type(local_file.fileName)[0]
            storage_backend, storage_path, size = self._get_local_file_info(local_file)

            image = ImageFile(event_id=event.id,
                              filename=local_file.fileName,
                              content_type=content_type,
                              created_dt=now_utc(),
                              size=size,
                              storage_backend=storage_backend,
                              storage_file_id=storage_path)

            db.session.add(image)
            db.session.flush()

            map_entry = LegacyImageMapping(event_id=event.id, legacy_image_id=local_file.id, image_id=image.id)

            db.session.add(map_entry)

            self.print_success(cformat('%{cyan}[{}]%{reset} -> %{blue!}{}').format(
                local_file.id, local_file.fileName, image), event_id=event.id)

    def _dt_with_tz(self, dt):
        if dt.tzinfo is not None:
            return dt
        server_tz = get_timezone(getattr(self.zodb_root['MaKaCInfo']['main'], '_timezone', 'UTC'))
        return server_tz.localize(dt).astimezone(pytz.utc)

    def _iter_pictures(self):
        for dmgr in self.flushing_iterator(self.zodb_root['displayRegistery'].itervalues()):
            imgr = getattr(dmgr, '_imagesMngr', None)
            event_id = dmgr._conf.id

            if imgr:
                if not Event.find_first(id=event_id):
                    self.print_warning('Event does not exist (anymore)!', event_id=event_id)
                else:
                    for _, picture in imgr._picList.iteritems():
                        yield dmgr._conf, picture
            else:
                self.print_warning('No _imagesMngr attribute!', event_id=event_id)
