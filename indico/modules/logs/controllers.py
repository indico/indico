# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, request

from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import preprocess_ts_string
from indico.modules.categories.controllers.base import RHManageCategoryBase
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.logs.models.entries import CategoryLogEntry, CategoryLogRealm, EventLogEntry, EventLogRealm
from indico.modules.logs.util import serialize_log_entry
from indico.modules.logs.views import WPCategoryLogs, WPEventLogs
from indico.web.flask.util import url_for


LOG_PAGE_SIZE = 15


def _contains(field, text):
    return (db.func.to_tsvector('simple', db.func.indico.indico_unaccent(field))
            .match(db.func.indico.indico_unaccent(preprocess_ts_string(text)), postgresql_regconfig='simple'))


def _get_metadata_query():
    return {k[len('meta.'):]: int(v) if v.isdigit() else v
            for k, v in request.args.items()
            if k.startswith('meta.')}


class RHEventLogs(RHManageEventBase):
    """Show the modification/action log for the event."""

    def _process(self):
        metadata_query = _get_metadata_query()
        realms = {realm.name: realm.title for realm in EventLogRealm}
        return WPEventLogs.render_template('logs.html', self.event, realms=realms, metadata_query=metadata_query,
                                           logs_api_url=url_for('.api_event_logs', self.event))


class RHCategoryLogs(RHManageCategoryBase):
    """Show the modification/action log for the category."""

    def _process(self):
        metadata_query = _get_metadata_query()
        realms = {realm.name: realm.title for realm in CategoryLogRealm}
        return WPCategoryLogs.render_template('logs.html', self.category, 'logs',
                                              realms=realms, metadata_query=metadata_query,
                                              logs_api_url=url_for('.api_category_logs', self.category))


class LogsAPIMixin:
    model = None
    realm_enum = None

    @property
    def object(self):
        raise NotImplementedError

    def _process(self):
        page = int(request.args.get('page', 1))
        filters = request.args.getlist('filters')
        metadata_query = _get_metadata_query()
        text = request.args.get('q')

        if not filters and not metadata_query:
            return jsonify(current_page=1, pages=[], entries=[], total_page_count=0)

        query = self.object.log_entries.order_by(self.model.logged_dt.desc())
        realms = {self.realm_enum.get(f) for f in filters if self.realm_enum.get(f)}
        if realms:
            query = query.filter(self.model.realm.in_(realms))

        if text:
            query = query.filter(
                db.or_(_contains(self.model.module, text),
                       _contains(self.model.type, text),
                       _contains(self.model.summary, text),
                       _contains(db.m.User.first_name + ' ' + db.m.User.last_name, text),
                       _contains(self.model.data['body'].astext, text),
                       _contains(self.model.data['subject'].astext, text),
                       _contains(self.model.data['from'].astext, text),
                       _contains(self.model.data['to'].astext, text),
                       _contains(self.model.data['cc'].astext, text))
            ).outerjoin(db.m.User)

        if metadata_query:
            query = query.filter(self.model.meta.contains(metadata_query))

        query = query.paginate(page=page, per_page=LOG_PAGE_SIZE)
        entries = [dict(serialize_log_entry(entry), index=index, html=entry.render())
                   for index, entry in enumerate(query.items)]
        return jsonify(current_page=page, pages=list(query.iter_pages()), total_page_count=query.pages, entries=entries)


class RHEventLogsJSON(LogsAPIMixin, RHManageEventBase):
    model = EventLogEntry
    realm_enum = EventLogRealm

    @property
    def object(self):
        return self.event


class RHCategoryLogsJSON(LogsAPIMixin, RHManageCategoryBase):
    model = CategoryLogEntry
    realm_enum = CategoryLogRealm

    @property
    def object(self):
        return self.category
