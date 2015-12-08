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

import random

from flask import request, jsonify
from werkzeug.exceptions import BadRequest

from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.modules.events.sessions.controllers.management import RHManageSessionsBase, RHManageSessionBase
from indico.modules.events.sessions.forms import SessionForm
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.operations import create_session, update_session, delete_session
from indico.modules.events.sessions.util import get_colors, get_active_sessions
from indico.modules.events.sessions.views import WPManageSessions
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form


def _get_session_list_args(event):
    return {'sessions': get_active_sessions(event), 'default_colors': get_colors()}


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
        form = SessionForm(obj=FormDefaults(colors=self._get_random_color()))
        if form.validate_on_submit():
            create_session(self.event_new, form.data)
            return jsonify_data(html=_render_session_list(self.event_new))
        return jsonify_form(form)


class RHModifySession(RHManageSessionBase):
    """Modify a session"""

    def _process(self):
        form = SessionForm(obj=self.session)
        if form.validate_on_submit():
            update_session(self.session, form.data)
            return jsonify_data(html=_render_session_list(self.event_new))
        return jsonify_form(form)


class RHDeleteSessions(RHManageSessionsBase):
    """Remove multiple sessions"""

    def _process(self):
        session_ids = map(int, request.form.getlist('session_id'))
        sessions = self.event_new.sessions.filter(Session.id.in_(session_ids), ~Session.is_deleted)
        for sess in sessions:
            delete_session(sess)
        return jsonify_data(html=_render_session_list(self.event_new))


class RHExportSessionsCSV(RHManageSessionsBase):
    """Export list of sessions to a CSV"""

    def _process(self):
        pass


class RHExportSessionsPDF(RHManageSessionsBase):
    """Export list of sessions to a PDF"""

    def _process(self):
        pass


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
