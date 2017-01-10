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

from operator import attrgetter

import click

from indico.core.db import db
from indico.modules.events.notes.models.notes import EventNote, RenderMode
from indico.modules.users import User
from indico.util.console import cformat, verbose_iterator
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import get_archived_file


class EventNoteImporter(Importer):
    def __init__(self, **kwargs):
        self.archive_dirs = kwargs.pop('archive_dir')
        self.janitor_user_id = kwargs.pop('janitor_user_id')
        super(EventNoteImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--archive-dir', required=True, multiple=True,
                               help="The base path where materials are stored (ArchiveDir in indico.conf). "
                                    "When used multiple times, the dirs are checked in order until a file is "
                                    "found.")(command)
        command = click.option('--janitor-user-id', type=int, required=True, help="The ID of the Janitor user")(command)
        return command

    def has_data(self):
        return EventNote.query.has_rows()

    def migrate(self):
        self.migrate_event_notes()

    def migrate_event_notes(self):
        self.print_step('migrating event notes')

        janitor_user = User.get_one(self.janitor_user_id)
        self.print_msg('Using janitor user {}'.format(janitor_user), always=True)
        for event, obj, minutes, special_prot in committing_iterator(self._iter_minutes()):
            if special_prot:
                self.print_warning(
                    cformat('%{yellow!}{} minutes have special permissions; skipping them').format(obj),
                    event_id=event.id
                )
                continue
            path = get_archived_file(minutes, self.archive_dirs)[1]
            if path is None:
                self.print_error(cformat('%{red!}{} minutes not found on disk; skipping them').format(obj),
                                 event_id=event.id)
                continue
            with open(path, 'r') as f:
                data = convert_to_unicode(f.read()).strip()
            if not data:
                self.print_warning(cformat('%{yellow}{} minutes are empty; skipping them').format(obj),
                                   always=False, event_id=event.id)
                continue
            note = EventNote(linked_object=obj)
            note.create_revision(RenderMode.html, data, janitor_user)
            db.session.add(note)
            if not self.quiet:
                self.print_success(cformat('%{cyan}{}').format(obj), event_id=event.id)

    def _has_special_protection(self, material, resource):
        material_ac = material._Material__ac
        resource_ac = resource._Resource__ac
        # both inherit
        if resource_ac._accessProtection == 0 and material_ac._accessProtection == 0:
            return False
        # resource is protected
        if resource_ac._accessProtection > 0:
            return True
        # material is protected and resource inherits
        if resource_ac._accessProtection == 0 and material_ac._accessProtection > 0:
            return True
        return False

    def _get_minutes(self, obj):
        material = obj.minutes
        if material is None:
            return None, None
        if material.file is None:
            return None, None
        return material.file, self._has_special_protection(material, material.file)

    def _iter_minutes(self):
        it = self.zodb_root['conferences'].itervalues()
        if self.quiet:
            it = verbose_iterator(it, len(self.zodb_root['conferences']), attrgetter('id'), attrgetter('title'))
        for event in self.flushing_iterator(it):
            minutes, special = self._get_minutes(event)
            if minutes:
                yield event, event, minutes, special
            for session in event.sessions.itervalues():
                minutes, special = self._get_minutes(session)
                if minutes:
                    yield event, session, minutes, special
            for contrib in event.contributions.itervalues():
                minutes, special = self._get_minutes(contrib)
                if minutes:
                    yield event, contrib, minutes, special
                for subcontrib in contrib._subConts:
                    minutes, special = self._get_minutes(subcontrib)
                    if minutes:
                        yield event, subcontrib, minutes, special
