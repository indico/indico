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

import mimetypes
from operator import attrgetter

import click
import pytz
from babel.dates import get_timezone

from indico.core.db import db
from indico.modules.events.models.events import Event
from indico.modules.events.layout.models.images import ImageFile
from indico.modules.events.layout.models.legacy_mapping import LegacyImageMapping
from indico.util.console import cformat, verbose_iterator
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import LocalFileImporterMixin


class EventImageImporter(LocalFileImporterMixin, Importer):
    def __init__(self, **kwargs):
        self.silence_old_events = kwargs.pop('silence_old_events')
        kwargs = self._set_config_options(**kwargs)
        super(EventImageImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--silence-old-events', is_flag=True,
                               help="Don't mention any schema abnormalities in old events")(command)
        command = super(EventImageImporter, EventImageImporter).decorate_command(command)
        return command

    def has_data(self):
        return ImageFile.query.has_rows()

    def migrate(self):
        self.migrate_event_images()

    def migrate_event_images(self):
        self.print_step('migrating event images')
        for event, picture in committing_iterator(self._iter_pictures()):
            local_file = picture._localFile
            content_type = mimetypes.guess_type(local_file.fileName)[0] or 'application/octet-stream'
            storage_backend, storage_path, size = self._get_local_file_info(local_file)

            if storage_path is None:
                self.print_warning(cformat('%{yellow}[{}]%{reset} -> %{red!}Not found in filesystem').format(
                    local_file.id), event_id=event.id)
                continue

            filename = secure_filename(convert_to_unicode(local_file.fileName), 'image')
            image = ImageFile(event_id=event.id,
                              filename=filename,
                              content_type=content_type,
                              created_dt=now_utc(),
                              size=size,
                              storage_backend=storage_backend,
                              storage_file_id=storage_path)

            db.session.add(image)
            db.session.flush()

            map_entry = LegacyImageMapping(event_id=event.id, legacy_image_id=local_file.id, image_id=image.id)

            db.session.add(map_entry)

            if not self.quiet:
                self.print_success(cformat('%{cyan}[{}]%{reset} -> %{blue!}{}').format(local_file.id, image),
                                   event_id=event.id)

    def _dt_with_tz(self, dt):
        if dt.tzinfo is not None:
            return dt
        server_tz = get_timezone(getattr(self.zodb_root['MaKaCInfo']['main'], '_timezone', 'UTC'))
        return server_tz.localize(dt).astimezone(pytz.utc)

    def _iter_pictures(self):
        it = iter(db.session.query(Event.id))
        if self.quiet:
            it = verbose_iterator(it, Event.query.count(), attrgetter('id'),
                                  lambda x: self.zodb_root['conferences'][str(x.id)].title, 100)
        for event_id, in self.flushing_iterator(it):
            try:
                dmgr = self.zodb_root['displayRegistery'][str(event_id)]
            except KeyError:
                self.print_error('Skipping event with no displaymgr', event_id=event_id)
                continue
            imgr = getattr(dmgr, '_imagesMngr', None)

            if imgr:
                for _, picture in imgr._picList.iteritems():
                    yield dmgr._conf, picture
            else:
                if not self.silence_old_events:
                    self.print_warning('No _imagesMngr attribute!', event_id=event_id)
