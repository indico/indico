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

from datetime import timedelta

import pytz
from babel.dates import get_timezone

from indico.core.config import Config
from indico.core.db import db
from indico.modules.events.reminders.models.reminders import EventReminder
from indico.util.console import cformat
from indico.util.date_time import now_utc
from indico.util.string import is_legacy_id
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer, convert_to_unicode


class EventAlarmImporter(Importer):
    def has_data(self):
        return EventReminder.query.has_rows()

    def migrate(self):
        self.migrate_event_alarms()

    def migrate_event_alarms(self):
        print cformat('%{white!}migrating event alarms/reminders')
        sent_threshold = now_utc() - timedelta(days=1)
        for event, alarm in committing_iterator(self._iter_alarms()):
            if is_legacy_id(event.id):
                print cformat('%{red!}!!!%{reset} '
                              '%{white!}{:6s}%{reset} %{yellow!}Event has non-numeric/broken ID').format(event.id)
                continue
            elif not alarm.startDateTime:
                print cformat('%{red!}!!!%{reset} '
                              '%{white!}{:6s}%{reset} %{yellow!}Alarm has no start time').format(event.id)
                continue
            start_dt = self._dt_with_tz(alarm.startDateTime).replace(second=0, microsecond=0)
            if not hasattr(alarm, 'status'):
                # Those ancient alarms can be safely assumed to be sent
                is_sent = True
            else:
                is_sent = alarm.status not in {1, 2}  # not spooled/queued
            is_overdue = False
            if not is_sent and start_dt < sent_threshold:
                is_sent = True
                is_overdue = True
            recipients = filter(None, {convert_to_unicode(x).strip().lower() for x in alarm.toAddr})
            reminder = EventReminder(event_id=int(event.id), creator_id=Config.getInstance().getJanitorUserId(),
                                     created_dt=alarm.createdOn, scheduled_dt=start_dt, is_sent=is_sent,
                                     event_start_delta=getattr(alarm, '_relative', None), recipients=recipients,
                                     send_to_participants=alarm.toAllParticipants,
                                     include_summary=alarm.confSumary,
                                     reply_to_address=convert_to_unicode(alarm.fromAddr).strip().lower(),
                                     message=convert_to_unicode(alarm.note).strip())
            db.session.add(reminder)
            status = (cformat('%{red!}OVERDUE%{reset}') if is_overdue else
                      cformat('%{green!}SENT%{reset}') if is_sent else
                      cformat('%{yellow}PENDING%{reset}'))
            print cformat('%{green}+++%{reset} '
                          '%{white!}{:6s}%{reset} %{cyan}{}%{reset} {}').format(event.id, reminder.scheduled_dt, status)

    def _dt_with_tz(self, dt):
        if dt.tzinfo is not None:
            return dt
        server_tz = get_timezone(getattr(self.zodb_root['MaKaCInfo']['main'], '_timezone', 'UTC'))
        return server_tz.localize(dt).astimezone(pytz.utc)

    def _iter_alarms(self):
        for event in self.flushing_iterator(self.zodb_root['conferences'].itervalues()):
            if not hasattr(event, 'alarmList'):
                continue
            for alarm in event.alarmList.itervalues():
                yield event, alarm
