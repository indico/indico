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

from datetime import timedelta, datetime
from operator import attrgetter

from indico.core.db import db
from indico.modules.events.logs import EventLogEntry, EventLogRealm, EventLogKind
from indico.modules.users import User
from indico.util.console import cformat, verbose_iterator
from indico.util.date_time import format_human_timedelta, format_datetime
from indico.util.string import seems_html
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer, convert_to_unicode


def _convert_data(event, value):
    if isinstance(value, timedelta):
        value = format_human_timedelta(value)
    elif isinstance(value, datetime):
        value = format_datetime(value, locale='en_GB', timezone=event.timezone)
    elif value.__class__.__name__ == 'ContributionType':
        value = value._name
    elif value.__class__.__name__ == 'AbstractFieldContent':
        value = '{}: "{}"'.format(convert_to_unicode(value.field._caption), convert_to_unicode(value.value))
    return convert_to_unicode(value).strip()


class EventLogImporter(Importer):
    def has_data(self):
        return EventLogEntry.query.has_rows()

    def migrate(self):
        # load users so we avoid querying them in a loop
        self.users = {x[0]: x[0] for x in db.session.query(User.id).filter_by(is_deleted=False)}
        self.users.update(x for x in db.session.query(User.id, User.merged_into_id)
                                               .filter(User.is_deleted, User.merged_into_id != None))  # noqa
        with db.session.no_autoflush:
            self.migrate_event_logs()

    def migrate_event_logs(self):
        self.print_step('migrating event logs')
        msg_email = cformat('%{white!}{:6d}%{reset} %{cyan}{}')
        msg_action = cformat('%{white!}{:6d}%{reset} %{cyan!}{}')

        for event in committing_iterator(self._iter_events()):
            if not hasattr(event, '_logHandler'):
                self.print_error('Event has no log handler!', event_id=event.id)
                continue
            for item in event._logHandler._logLists['emailLog']:
                entry = self._migrate_email_log(event, item)
                db.session.add(entry)
                if not self.quiet:
                    self.print_success(msg_email.format(entry.event_id, entry))
            for item in event._logHandler._logLists['actionLog']:
                entry = self._migrate_action_log(event, item)
                db.session.add(entry)
                if not self.quiet:
                    self.print_success(msg_action.format(entry.event_id, entry))

    def _migrate_log(self, event, item):
        user_id = None
        if (item._responsibleUser and item._responsibleUser.__class__.__name__ in {'Avatar', 'AvatarUserWrapper'} and
                unicode(item._responsibleUser.id).isdigit()):
            user_id = self.users.get(int(item._responsibleUser.id))
        module = item._module or 'Unknown'
        if module.startswith('MaKaC/plugins/Collaboration'):
            module = 'Collaboration'
        elif module == 'chat' or module.startswith('MaKaC/plugins/InstantMessaging/XMPP'):
            module = 'Chat'
        elif module == 'vc_vidyo':
            module = 'Vidyo'
        elif module == 'Timetable/SubContribution':
            module = 'Timetable/Subcontribution'
        elif module.islower():
            module = module.title()
        entry = EventLogEntry(event=event, logged_dt=item._logDate, module=module, user_id=user_id,
                              kind=EventLogKind.other)
        return entry

    def _migrate_email_log(self, event, item):
        info = item._logInfo
        entry = self._migrate_log(event, item)
        entry.realm = EventLogRealm.emails
        entry.type = 'email'
        entry.summary = 'Sent email: {}'.format(convert_to_unicode(info['subject']).strip())
        content_type = convert_to_unicode(info.get('contentType')) or (
            'text/html' if seems_html(info['body']) else 'text/plain')
        entry.data = {
            'from': convert_to_unicode(info['fromAddr']),
            'to': map(convert_to_unicode, set(info['toList'])),
            'cc': map(convert_to_unicode, set(info['ccList'])),
            'bcc': map(convert_to_unicode, set(info.get('bccList', []))),
            'subject': convert_to_unicode(info['subject']),
            'body': convert_to_unicode(info['body']),
            'content_type': content_type,
        }
        return entry

    def _migrate_action_log(self, event, item):
        info = item._logInfo
        entry = self._migrate_log(event, item)
        entry.realm = EventLogRealm.event
        entry.type = 'simple'
        entry.summary = convert_to_unicode(info['subject']).strip()
        entry.data = {convert_to_unicode(k): _convert_data(event, v) for k, v in info.iteritems() if k != 'subject'}
        return entry

    def _iter_events(self):
        it = self.zodb_root['conferences'].itervalues()
        if self.quiet:
            it = verbose_iterator(it, len(self.zodb_root['conferences']), attrgetter('id'), attrgetter('title'), 25)
        return self.flushing_iterator(it)
