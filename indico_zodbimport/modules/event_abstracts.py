# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

import traceback
from datetime import timedelta
from operator import attrgetter

from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.settings import boa_settings, BOACorrespondingAuthorType, BOASortField
from indico.modules.events.models.events import EventType
from indico.util.console import verbose_iterator, cformat
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode


class AbstractMigration(object):
    def __init__(self, importer, conf, event):
        self.importer = importer
        self.conf = conf
        self.event = event
        self.amgr = conf.abstractMgr

    def __repr__(self):
        return '<AbstractMigration({})>'.format(self.event)

    def run(self):
        self._migrate_boa_settings()
        # TODO...

    def _migrate_boa_settings(self):
        boa_config = self.conf._boa
        sort_field_map = {'number': 'id', 'none': 'id', 'name': 'abstract_title', 'sessionTitle': 'session_title',
                          'speakers': 'speaker', 'submitter': 'id'}
        try:
            sort_by = sort_field_map.get(boa_config._sortBy, boa_config._sortBy)
        except AttributeError:
            sort_by = 'id'
        corresponding_author = getattr(boa_config, '_correspondingAuthor', 'submitter')
        boa_settings.set_multi(self.event, {
            'extra_text': convert_to_unicode(boa_config._text),
            'sort_by': BOASortField[sort_by],
            'corresponding_author': BOACorrespondingAuthorType[corresponding_author],
            'show_abstract_ids': bool(getattr(boa_config, '_showIds', False))
        })


class EventAbstractsImporter(Importer):
    def has_data(self):
        return Abstract.has_rows()

    def migrate(self):
        self.migrate_event_abstracts()

    def migrate_event_abstracts(self):
        self.print_step("Migrating event abstracts")
        for conf, event in committing_iterator(self._iter_events()):
            amgr = conf.abstractMgr
            duration = amgr._submissionEndDate - amgr._submissionStartDate
            if not amgr._activated and not amgr._abstracts and not amgr._notifTpls and duration < timedelta(minutes=1):
                continue
            mig = AbstractMigration(self, conf, event)
            try:
                with db.session.begin_nested():
                    with db.session.no_autoflush:
                        mig.run()
                        db.session.flush()
            except Exception:
                self.print_error(cformat('%{red!}MIGRATION FAILED!'), event_id=event.id)
                traceback.print_exc()
                raw_input('Press ENTER to continue')
            db.session.flush()

    def _iter_events(self):
        from sqlalchemy.orm import subqueryload
        query = (Event.query
                 .filter(~Event.is_deleted)
                 .filter(Event.legacy_abstracts.any() | (Event.type_ == EventType.conference))
                 .options(subqueryload('legacy_abstracts')))
        it = iter(query)
        if self.quiet:
            it = verbose_iterator(query, query.count(), attrgetter('id'), lambda x: '')
        confs = self.zodb_root['conferences']
        for event in it:
            yield confs[str(event.id)], event
