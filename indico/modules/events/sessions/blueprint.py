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

from indico.modules.events.sessions.controllers.management.protection import RHSessionCoordinatorPrivs
from indico.modules.events.sessions.controllers.management.sessions import (RHSessionsList, RHCreateSession,
                                                                            RHModifySession, RHDeleteSessions,
                                                                            RHExportSessionsCSV, RHExportSessionsExcel,
                                                                            RHExportSessionsPDF, RHSessionREST,
                                                                            RHSessionPersonList)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('sessions', __name__, template_folder='templates', virtual_template_folder='events/sessions',
                      url_prefix='/event/<confId>')

_bp.add_url_rule('/manage/sessions/', 'session_list', RHSessionsList)
_bp.add_url_rule('/manage/sessions/create', 'create_session', RHCreateSession, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/sessions/delete', 'delete_sessions', RHDeleteSessions, methods=('POST',))
_bp.add_url_rule('/manage/sessions/sessions.csv', 'export_csv', RHExportSessionsCSV, methods=('POST',))
_bp.add_url_rule('/manage/sessions/sessions.xlsx', 'export_excel', RHExportSessionsExcel, methods=('POST',))
_bp.add_url_rule('/manage/sessions/sessions.pdf', 'export_pdf', RHExportSessionsPDF, methods=('POST',))
_bp.add_url_rule('/manage/sessions/<int:session_id>', 'session_rest', RHSessionREST, methods=('PATCH', 'DELETE'))
_bp.add_url_rule('/manage/sessions/<int:session_id>/modify', 'modify_session', RHModifySession, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/sessions/person-list/', 'person_list', RHSessionPersonList, methods=('POST',))

_bp.add_url_rule('/manage/sessions/coordinator-privs/', 'coordinator_privs_rest', RHSessionCoordinatorPrivs)
_bp.add_url_rule('/manage/sessions/coordinator-privs/<priv>', 'coordinator_privs_rest', RHSessionCoordinatorPrivs,
                 methods=('PUT', 'DELETE'))
