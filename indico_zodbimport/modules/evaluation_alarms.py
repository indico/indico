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

import itertools
from datetime import date

from indico.modules.events.evaluation_old import event_settings as evaluation_settings
from indico.util.console import cformat
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer


class EvaluationAlarmImporter(Importer):
    def has_data(self):
        return bool(evaluation_settings.query.filter_by(name='send_notification').count())

    def migrate(self):
        self.migrate_evaluation_alarms()

    def migrate_evaluation_alarms(self):
        print cformat('%{white!}migrating evaluation alarms')

        today = date.today()
        for task in committing_iterator(self._iter_tasks('EvaluationAlarm')):
            start_date = task.conf._evaluations[0].startDate.date()
            if start_date < today:
                print cformat('%{yellow!}!!!%{reset} '
                              '%{white!}{:6d}%{reset} %{yellow}evaluation starts in the past ({})').format(
                    int(task.conf.id), start_date)
            elif not task.conf._evaluations[0].visible:
                print cformat('%{yellow!}!!!%{reset} '
                              '%{white!}{:6d}%{reset} %{yellow}evaluation is disabled').format(int(task.conf.id))
            else:
                print cformat('%{green}+++%{reset} '
                              '%{white!}{:6d}%{reset} %{cyan}{}').format(int(task.conf.id), start_date)
                evaluation_settings.set(task.conf, 'send_notification', True)

    def _iter_tasks(self, type_):
        scheduler_root = self.zodb_root['modules']['scheduler']
        return (t for t in itertools.chain.from_iterable(scheduler_root._waitingQueue._container.itervalues())
                if t.typeId == type_)
