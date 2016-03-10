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

import random

from flask import request, jsonify
from sqlalchemy.orm import subqueryload, undefer
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.management.controllers import RHContributionPersonListMixin
from indico.modules.events.sessions.controllers.management import (RHManageSessionsBase, RHManageSessionBase,
                                                                   RHManageSessionsActionsBase)
from indico.modules.events.sessions.forms import SessionForm, SessionProtectionForm
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.operations import create_session, update_session, delete_session
from indico.modules.events.sessions.util import (get_colors, generate_spreadsheet_from_sessions,
                                                 generate_pdf_from_sessions)
from indico.modules.events.sessions.views import WPManageSessions
from indico.modules.events.util import update_object_principals
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form


def _get_session_list_args(event):
    sessions = (event.sessions
                .options(undefer('attachment_count'),
                         subqueryload('blocks').undefer('contribution_count'))
                .order_by(db.func.lower(Session.title))
                .all())
    return {'sessions': sessions, 'default_colors': get_colors()}


def _render_session_list(event):
    tpl = get_template_module('events/sessions/management/_session_list.html')
    return tpl.render_session_list(event, **_get_session_list_args(event))


class RHSessionsList(RHManageSessionsBase):
    """Display list of all sessions within the event"""

    def _process(self):
        return WPManageSessions.render_template('management/session_list.html', self._conf,
                                                event=self.event_new, **_get_session_list_args(self.event_new))


class RHCreateSession(RHManageSessionsBase):
    """Create a session in the event"""

    def _get_random_color(self):
        used_colors = {s.colors for s in self.event_new.sessions.filter_by(is_deleted=False)}
        unused_colors = set(get_colors()) - used_colors
        return random.choice(tuple(unused_colors) or get_colors())

    def _process(self):
        inherited_location = self.event_new.location_data
        inherited_location['inheriting'] = True
        form = SessionForm(obj=FormDefaults(colors=self._get_random_color(), location_data=inherited_location))
        if form.validate_on_submit():
            new_session = create_session(self.event_new, form.data)
            sessions = [{'id': s.id, 'title': s.title, 'colors': s.colors}
                        for s in self.event_new.sessions.filter_by(is_deleted=False)]
            return jsonify_data(sessions=sessions, new_session_id=new_session.id,
                                html=_render_session_list(self.event_new))
        return jsonify_form(form)


class RHModifySession(RHManageSessionBase):
    """Modify a session"""

    def _process(self):
        form = SessionForm(obj=self.session)
        if form.validate_on_submit():
            update_session(self.session, form.data)
            return jsonify_data(html=_render_session_list(self.event_new))
        return jsonify_form(form)


class RHDeleteSessions(RHManageSessionsActionsBase):
    """Remove multiple sessions"""

    def _process(self):
        for sess in self.sessions:
            delete_session(sess)
        return jsonify_data(html=_render_session_list(self.event_new))


class RHExportSessionsCSV(RHManageSessionsActionsBase):
    """Export list of sessions to a CSV"""

    def _process(self):
        headers, rows = generate_spreadsheet_from_sessions(self.sessions)
        return send_csv('sessions.csv', headers, rows)


class RHExportSessionsExcel(RHManageSessionsActionsBase):
    """Export list of sessions to a XLSX"""

    def _process(self):
        headers, rows = generate_spreadsheet_from_sessions(self.sessions)
        return send_xlsx('sessions.xlsx', headers, rows)


class RHExportSessionsPDF(RHManageSessionsActionsBase):
    """Export list of sessions to a PDF"""

    def _process(self):
        pdf_file = generate_pdf_from_sessions(self.event_new, self.sessions)
        return send_file('sessions.pdf', pdf_file, 'application/pdf')


class RHSessionREST(RHManageSessionBase):
    """Perform update or removal of a session"""

    def _process_DELETE(self):
        delete_session(self.session)
        return jsonify_data(html=_render_session_list(self.event_new))

    def _process_PATCH(self):
        data = request.json
        updates = {}
        if data.viewkeys() > {'colors'}:
            raise BadRequest
        if 'colors' in data:
            colors = ColorTuple(**data['colors'])
            if colors not in get_colors():
                raise BadRequest
            updates['colors'] = colors
        update_session(self.session, updates)
        return jsonify()


class RHSessionPersonList(RHContributionPersonListMixin, RHManageSessionsActionsBase):
    """List of persons in the session's contributions"""

    @property
    def _membership_filter(self):
        session_ids = {s.id for s in self.sessions}
        return Contribution.session_id.in_(session_ids)


class RHSessionProtection(RHManageSessionBase):
    """Manage session protection"""

    def _process(self):
        form = SessionProtectionForm(obj=FormDefaults(**self._get_defaults()), session=self.session,
                                     prefix='session-protection-')
        if form.validate_on_submit():
            update_session(self.session, {'protection_mode': form.protection_mode.data})
            if self.session.is_protected:
                update_object_principals(self.session, form.acl.data, read_access=True)
            update_object_principals(self.session, form.managers.data, full_access=True)
            update_object_principals(self.session, form.coordinators.data, role='coordinate')
            return jsonify_data(flash=False, html=_render_session_list(self.event_new))
        return jsonify_form(form)

    def _get_defaults(self):
        acl = {x.principal for x in self.session.acl_entries if x.read_access}
        managers = {x.principal for x in self.session.acl_entries if x.full_access}
        coordinators = {x.principal for x in self.session.acl_entries if x.has_management_role(role='coordinate')}
        return {'managers': managers, 'protection_mode': self.session.protection_mode, 'coordinators': coordinators,
                'acl': acl}
