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


from __future__ import unicode_literals, division

import re
from operator import attrgetter

from indico.modules.events.models.events import Event
from indico.modules.events.models.settings import EventSetting
from indico.modules.events.settings import event_core_settings, event_contact_settings
from indico.util.console import verbose_iterator
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode


SPLIT_EMAILS_RE = re.compile(r'[\s;,]+')
SPLIT_PHONES_RE = re.compile(r'[/;,]+')


class EventDataImporter(Importer):
    def has_data(self):
        return (EventSetting.query.filter(EventSetting.module.in_(['core', 'contact'])).has_rows() or
                Event.query.filter_by(is_locked=True).has_rows())

    def migrate(self):
        self.migrate_event_data()

    def migrate_event_data(self):
        self.print_step("Migrating event data")
        for conf in committing_iterator(self._iter_events()):
            event_id = int(conf.id)
            if conf._screenStartDate:
                event_core_settings.set(event_id, 'start_dt_override', conf._screenStartDate)
            if conf._screenEndDate:
                event_core_settings.set(event_id, 'end_dt_override', conf._screenEndDate)
            organizer_info = convert_to_unicode(conf._orgText)
            if organizer_info:
                event_core_settings.set(event_id, 'organizer_info', organizer_info)
            additional_info = convert_to_unicode(conf.contactInfo)
            if additional_info:
                event_core_settings.set(event_id, 'additional_info', additional_info)
            si = conf._supportInfo
            contact_title = convert_to_unicode(si._caption)
            contact_email = convert_to_unicode(si._email)
            contact_phone = convert_to_unicode(si._telephone)
            contact_emails = map(unicode.strip, SPLIT_EMAILS_RE.split(contact_email)) if contact_email else []
            contact_phones = map(unicode.strip, SPLIT_PHONES_RE.split(contact_phone)) if contact_phone else []
            if contact_title:
                event_contact_settings.set(event_id, 'title', contact_title)
            if contact_emails:
                event_contact_settings.set(event_id, 'emails', contact_emails)
            if contact_phones:
                event_contact_settings.set(event_id, 'phones', contact_phones)
            if conf._closed:
                Event.query.filter_by(id=event_id).update({Event.is_locked: True}, synchronize_session=False)

    def _iter_events(self):
        it = self.zodb_root['conferences'].itervalues()
        total = len(self.zodb_root['conferences'])
        it = verbose_iterator(it, total, attrgetter('id'), lambda x: '')
        for conf in self.flushing_iterator(it):
            yield conf
