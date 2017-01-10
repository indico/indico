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

import transaction

from indico.util.console import verbose_iterator
from indico_zodbimport import Importer


class EventAbstractZODBPatcher(Importer):

    def migrate(self):
        self.patch_judgments()

    def _zodb_committing_iterator(self, iterable):
        for i, data in enumerate(iterable, 1):
            yield data
            if i % 100 == 0:
                transaction.commit()
        transaction.commit()

    def patch_judgments(self):
        self.print_step('patching AbstractJudgement objects')

        for event, abstract in self._zodb_committing_iterator(self._iter_abstracts()):
            history = getattr(abstract, '_trackJudgementsHistorical', None)
            if history is None:
                self.print_warning('Abstract {} has no judgment history'.format(abstract._id),
                                   event_id=event.id)
                continue
            if not hasattr(history, 'iteritems'):
                abstract._trackJudgementsHistorical = {}
                self.print_warning('Abstract {} had corrupt judgment history. Fixed.'.format(abstract._id),
                                   event_id=event.id)
                continue
            for track_id, judgments in history.iteritems():
                for judgment in judgments:
                    judgment._abstract = abstract

    def _iter_abstracts(self):
        old_events = self.zodb_root['conferences']
        for old_event in verbose_iterator(old_events.itervalues(), len(old_events), attrgetter('id'),
                                          lambda x: ''):
            for abstract in old_event.abstractMgr._abstracts.itervalues():
                yield old_event, abstract
