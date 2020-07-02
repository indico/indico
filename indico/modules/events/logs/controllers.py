# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import jsonify, request

from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import preprocess_ts_string
from indico.modules.events.logs.models.entries import EventLogEntry, EventLogRealm
from indico.modules.events.logs.util import serialize_log_entry
from indico.modules.events.logs.views import WPEventLogs
from indico.modules.events.management.controllers import RHManageEventBase


LOG_PAGE_SIZE = 15


def _contains(field, text):
    return (db.func.to_tsvector('simple', db.func.indico.indico_unaccent(field))
            .match(db.func.indico.indico_unaccent(preprocess_ts_string(text)), postgresql_regconfig='simple'))


def _get_metadata_query():
    return {k[len('meta.'):]: int(v) if v.isdigit() else v
            for k, v in request.args.iteritems()
            if k.startswith('meta.')}


class RHEventLogs(RHManageEventBase):
    """Shows the modification/action log for the event"""

    def _process(self):
        metadata_query = _get_metadata_query()
        realms = {realm.name: realm.title for realm in EventLogRealm}
        return WPEventLogs.render_template('logs.html', self.event, realms=realms, metadata_query=metadata_query)


class RHEventLogsJSON(RHManageEventBase):
    def _process(self):
        page = int(request.args.get('page', 1))
        filters = request.args.getlist('filters')
        metadata_query = _get_metadata_query()
        text = request.args.get('q')

        if not filters and not metadata_query:
            return jsonify(current_page=1, pages=[], entries=[], total_page_count=0)

        query = self.event.log_entries.order_by(EventLogEntry.logged_dt.desc())
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

        if metadata_query:
            query = query.filter(EventLogEntry.meta.contains(metadata_query))

        query = query.paginate(page, LOG_PAGE_SIZE)
        entries = [dict(serialize_log_entry(entry), index=index, html=entry.render())
                   for index, entry in enumerate(query.items)]
        return jsonify(current_page=page, pages=list(query.iter_pages()), total_page_count=query.pages, entries=entries)
