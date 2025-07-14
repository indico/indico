# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from babel.dates import get_timezone
from flask import flash, jsonify, redirect, request, session
from werkzeug.exceptions import BadRequest, Forbidden

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import preprocess_ts_string
from indico.core.notifications import make_email, send_email
from indico.modules.admin import RHAdminBase
from indico.modules.categories.controllers.base import RHManageCategoryBase
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.logs.models.entries import (AppLogEntry, AppLogRealm, CategoryLogEntry, CategoryLogRealm,
                                                EventLogEntry, EventLogRealm, UserLogEntry, UserLogRealm)
from indico.modules.logs.util import serialize_log_entry
from indico.modules.logs.views import WPAppLogs, WPCategoryLogs, WPEventLogs, WPUserLogs
from indico.modules.users.controllers import RHUserBase
from indico.util.i18n import _
from indico.web.flask.util import url_for


LOG_PAGE_SIZE = 15


def _contains(field, text):
    return (db.func.to_tsvector('simple', db.func.indico.indico_unaccent(field))
            .match(db.func.indico.indico_unaccent(preprocess_ts_string(text)), postgresql_regconfig='simple'))


def _get_metadata_query():
    return {k[len('meta.'):]: int(v) if v.isdigit() else v
            for k, v in request.args.items()
            if k.startswith('meta.')}


class RHAppLogs(RHAdminBase):
    """Show app logs."""

    def _process(self):
        metadata_query = _get_metadata_query()
        realms = {realm.name: realm.title for realm in AppLogRealm}
        return WPAppLogs.render_template('logs.html', 'logs',
                                         realms=realms, metadata_query=metadata_query,
                                         logs_api_url=url_for('.api_app_logs'))


class RHCategoryLogs(RHManageCategoryBase):
    """Show the modification/action log for the category."""

    def _process(self):
        metadata_query = _get_metadata_query()
        realms = {realm.name: realm.title for realm in CategoryLogRealm}
        return WPCategoryLogs.render_template('logs.html', self.category, 'logs',
                                              realms=realms, metadata_query=metadata_query,
                                              logs_api_url=url_for('.api_category_logs', self.category))


class RHEventLogs(RHManageEventBase):
    """Show the modification/action log for the event."""

    def _process(self):
        metadata_query = _get_metadata_query()
        realms = {realm.name: realm.title for realm in EventLogRealm}
        return WPEventLogs.render_template('logs.html', self.event, realms=realms, metadata_query=metadata_query,
                                           logs_api_url=url_for('.api_event_logs', self.event))


class RHUserLogs(RHUserBase):
    """Show the modification/action log for the user."""

    def _check_access(self):
        RHUserBase._check_access(self)
        if not session.user.is_admin:
            raise Forbidden

    def _process(self):
        metadata_query = _get_metadata_query()
        realms = {realm.name: realm.title for realm in UserLogRealm}
        return WPUserLogs.render_template('logs.html', 'logs', user=self.user,
                                          realms=realms, metadata_query=metadata_query,
                                          logs_api_url=url_for('.api_user_logs', self.user))


class LogsAPIMixin:
    model = None
    realm_enum = None

    @property
    def object(self):
        raise NotImplementedError

    @property
    def object_tzinfo(self):
        raise NotImplementedError

    def _process(self):
        page = int(request.args.get('page', 1))
        filters = request.args.getlist('filters')
        metadata_query = _get_metadata_query()
        text = request.args.get('q')

        if not filters and not metadata_query:
            return jsonify(current_page=1, pages=[], entries=[], total_page_count=0)

        query = self.object.log_entries if self.object else self.model.query
        query = query.order_by(self.model.logged_dt.desc())
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
            ).outerjoin(db.m.User, db.m.User.id == self.model.user_id)

        if metadata_query:
            query = query.filter(self.model.meta.contains(metadata_query))

        query = query.paginate(page=page, per_page=LOG_PAGE_SIZE)
        tzinfo = self.object_tzinfo
        entries = [dict(serialize_log_entry(entry, tzinfo), index=index, html=entry.render())
                   for index, entry in enumerate(query.items)]
        return jsonify(current_page=page, pages=list(query.iter_pages()), total_page_count=query.pages, entries=entries)


class RHAppLogsJSON(LogsAPIMixin, RHAdminBase):
    model = AppLogEntry
    realm_enum = AppLogRealm

    @property
    def object(self):
        return None

    @property
    def object_tzinfo(self):
        return get_timezone(config.DEFAULT_TIMEZONE)


class RHCategoryLogsJSON(LogsAPIMixin, RHManageCategoryBase):
    model = CategoryLogEntry
    realm_enum = CategoryLogRealm

    @property
    def object(self):
        return self.category

    @property
    def object_tzinfo(self):
        return self.category.tzinfo


class RHEventLogsJSON(LogsAPIMixin, RHManageEventBase):
    model = EventLogEntry
    realm_enum = EventLogRealm

    @property
    def object(self):
        return self.event

    @property
    def object_tzinfo(self):
        return self.event.tzinfo


class RHUserLogsJSON(LogsAPIMixin, RHUserBase):
    model = UserLogEntry
    realm_enum = UserLogRealm

    @property
    def object(self):
        return self.user

    @property
    def object_tzinfo(self):
        return get_timezone(config.DEFAULT_TIMEZONE)


class RHResendEmail(RHManageEventBase):
    """Resend an email log entry."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.entry
        }
    }

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.entry = (EventLogEntry.query
                      .with_parent(self.event)
                      .filter_by(id=request.view_args['log_entry_id'])
                      .first_or_404())

    def _process(self):
        if self.entry.type != 'email':
            raise BadRequest('Invalid log entry type')
        elif self.entry.data.get('attachments'):
            raise BadRequest('Cannot re-send email with attachments')
        email = make_email(
            to_list=self.entry.data['to'],
            cc_list=self.entry.data.get('cc', []),
            bcc_list=self.entry.data.get('bcc', []),
            sender_address=self.entry.data['from'],
            reply_address=self.entry.data.get('reply_to', []),
            subject=self.entry.data['subject'],
            body=self.entry.data['body'],
            html=self.entry.data['content_type'] == 'text/html',
        )
        send_email(email, event=self.event, module=self.entry.module, user=self.entry.user,
                   log_metadata=self.entry.meta, log_summary=f'Resent email: {self.entry.data['subject']}')
        flash(_('The email has been re-sent.'), 'success')
        return redirect(url_for('.event', self.event))
