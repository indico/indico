# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from collections import defaultdict

from flask import jsonify, request

from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import preprocess_ts_string
from indico.modules.events.logs.models.entries import EventLogEntry, EventLogRealm
from indico.modules.events.logs.util import serialize_log_entry
from indico.modules.events.logs.views import WPEventLogs
from indico.modules.events.management.controllers import RHManageEventBase


LOG_PAGE_SIZE = 10


def _contains(field, text):
    return db.func.to_tsvector('simple', field).match(preprocess_ts_string(text),
                                                      postgresql_regconfig='simple')


class RHEventLogs(RHManageEventBase):
    """Shows the modification/action log for the event"""

    def _process(self):
        entries = self.event.log_entries.order_by(EventLogEntry.logged_dt.desc()).all()
        realms = {e.realm for e in entries}
        all_realms = [{'name': realm.name, 'title': realm.title} for realm in EventLogRealm]
        return WPEventLogs.render_template('logs.html', self.event, entries=entries, realms=realms,
                                           all_realms=all_realms)


class RHEventLogsJSON(RHManageEventBase):
    def _process(self):
        entries = defaultdict(list)
        page = int(request.args.get('page', 1))
        filters = request.args.getlist('filters')
        text = request.args.get('q')

        query = self.event.log_entries.order_by(EventLogEntry.logged_dt.desc())

        if filters:
            realms = {EventLogRealm.get(f) for f in filters if EventLogRealm.get(f)}
            if realms:
                query = query.filter(EventLogEntry.realm.in_(realms))

        if text:
            query = query.filter(
                db.or_(_contains(EventLogEntry.module, text),
                       _contains(EventLogEntry.type, text),
                       _contains(EventLogEntry.summary, text),
                       _contains(db.m.User.first_name + " " + db.m.User.last_name, text),
                       _contains(EventLogEntry.data['body'].astext, text),
                       _contains(EventLogEntry.data['subject'].astext, text),
                       _contains(EventLogEntry.data['from'].astext, text),
                       _contains(EventLogEntry.data['to'].astext, text),
                       _contains(EventLogEntry.data['cc'].astext, text))
            ).outerjoin(db.m.User)

        query = query.paginate(page, LOG_PAGE_SIZE)

        for entry in query.items:
            day = entry.logged_dt.date()
            entries[day.isoformat()].append(serialize_log_entry(entry))
        return jsonify(current_page=page, pages=list(query.iter_pages()), entries=entries)
