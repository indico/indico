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

from operator import attrgetter

import transaction

from indico.core.db import db, DBMgr
from indico.modules.events.models.legacy_mapping import LegacyEventMapping
from indico.modules.events.models.settings import EventSetting, EventSettingPrincipal
from indico.modules.fulltextindexes.models.events import IndexedEvent
from indico.util.console import cformat, verbose_iterator
from indico_zodbimport import Importer
from MaKaC.webinterface.displayMgr import ConfDisplayMgrRegistery
from MaKaC.webinterface.internalPagesMgr import InternalPagesMgrRegistery
from MaKaC.webinterface.webFactoryRegistry import WebFactoryRegistry


class Dummy(object):
    pass


class ImporterDBMgr(DBMgr):
    def __init__(self, zodb_root):
        self._db = zodb_root
        self._conn = Dummy()
        self._conn.conn = zodb_root._p_jar


class LegacyEventImporter(Importer):
    def has_data(self):
        return bool(LegacyEventMapping.query.count())

    def migrate(self):
        DBMgr.setInstance(ImporterDBMgr(self.zodb_root))
        self.migrate_legacy_events()

    def migrate_legacy_events(self):
        print cformat('%{white!}migrating legacy events')

        dmr = ConfDisplayMgrRegistery()._getDisplayMgrRegistery()
        wfr = WebFactoryRegistry()._getConfRegistry()
        ipmr = InternalPagesMgrRegistery()._getInternalPagesMgrRegistery()
        for event in self._committing_iterator(self._get_events()):
            if not hasattr(event, '_old_id'):
                new_id = self.gen_event_id()
                event.unindexConf()
                del self.zodb_root['conferences'][event.id]
                dm = dmr.pop(event.id, None)
                wf = wfr.pop(event.id, None)
                ipm = ipmr.pop(event.id, None)
                event._old_id = event.id
                event.id = new_id
                if dm is not None:
                    dmr[event.id] = dm
                if wf is not None:
                    wfr[event.id] = wf
                if ipm is not None:
                    ipmr[event.id] = ipm
                self.zodb_root['conferences'][event.id] = event
                event.indexConf()
                IndexedEvent.find(id=event._old_id).update({IndexedEvent.id: event.id})
                EventSetting.find(event_id=event._old_id).update({EventSetting.event_id: event.id})
                EventSettingPrincipal.find(event_id=event._old_id).update({EventSettingPrincipal.event_id: event.id})
                db.session.add(LegacyEventMapping(legacy_event_id=event._old_id, event_id=int(event.id)))
                if not self.quiet:
                    self.print_success(cformat('%{cyan}{}').format(event.id), event_id=event._old_id)
            else:
                # happens if this importer was executed before but you want to add the mapping to your DB again
                db.session.add(LegacyEventMapping(legacy_event_id=event._old_id, event_id=int(event.id)))
                if not self.quiet:
                    self.print_success(cformat('%{cyan}{}%{reset} %{yellow}(already updated in zodb)').format(event.id),
                                       event_id=event._old_id)

    def gen_event_id(self):
        counter = self.zodb_root['counters']['CONFERENCE']
        rv = str(counter._Counter__count)
        counter._Counter__count += 1
        return rv

    def _get_events(self):
        # we modify the conferences dict so we can't iterate over it while doing so
        events = self.flushing_iterator(self.zodb_root['conferences'].itervalues())
        events = verbose_iterator(events, len(self.zodb_root['conferences']), attrgetter('id'), attrgetter('title'))
        return [event for event in events if event.has_legacy_id or hasattr(event, '_old_id')]

    def _committing_iterator(self, iterable):
        for i, data in enumerate(iterable, 1):
            yield data
            if i % 1000 == 0:
                db.session.commit()
                transaction.commit()
        db.session.commit()
        transaction.commit()
