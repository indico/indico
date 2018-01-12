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

from functools import partial

from indico.modules.events.sessions.controllers.compat import compat_session
from indico.modules.events.sessions.controllers.display import (RHDisplaySession, RHDisplaySessionList,
                                                                RHExportSessionTimetableToPDF, RHExportSessionToICAL)
from indico.modules.events.sessions.controllers.management.sessions import (RHCreateSession, RHDeleteSessions,
                                                                            RHExportSessionsCSV, RHExportSessionsExcel,
                                                                            RHExportSessionsPDF, RHManageSessionBlock,
                                                                            RHModifySession, RHSessionACL,
                                                                            RHSessionACLMessage, RHSessionBlocks,
                                                                            RHSessionPersonList, RHSessionProtection,
                                                                            RHSessionREST, RHSessionsList)
from indico.web.flask.util import make_compat_redirect_func
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
_bp.add_url_rule('/manage/sessions/<int:session_id>/blocks', 'session_blocks', RHSessionBlocks)
_bp.add_url_rule('/manage/sessions/<int:session_id>/modify', 'modify_session', RHModifySession, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/sessions/person-list/', 'person_list', RHSessionPersonList, methods=('POST',))
_bp.add_url_rule('/manage/sessions/<int:session_id>/protection', 'session_protection', RHSessionProtection,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/sessions/<int:session_id>/blocks/<int:block_id>', 'manage_session_block',
                 RHManageSessionBlock, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/sessions/<int:session_id>/acl', 'acl', RHSessionACL)
_bp.add_url_rule('/manage/sessions/<int:session_id>/acl-message', 'acl_message', RHSessionACLMessage)


# Display
_bp.add_url_rule('/sessions/mine', 'my_sessions', RHDisplaySessionList)
_bp.add_url_rule('/sessions/<int:session_id>/', 'display_session', RHDisplaySession)
_bp.add_url_rule('/sessions/<int:session_id>/session.ics', 'export_ics', RHExportSessionToICAL)
_bp.add_url_rule('/sessions/<int:session_id>/session-timetable.pdf', 'export_session_timetable',
                 RHExportSessionTimetableToPDF)

# Legacy URLs
_compat_bp = IndicoBlueprint('compat_sessions', __name__, url_prefix='/event/<event_id>')

_compat_bp.add_url_rule('/session/<legacy_session_id>/', 'session',
                        partial(compat_session, 'display_session'))
_compat_bp.add_url_rule('/session/<legacy_session_id>/session.ics', 'session_ics',
                        partial(compat_session, 'export_ics'))
_compat_bp.add_url_rule('/my-conference/sessions', 'my_sessions',
                        make_compat_redirect_func(_bp, 'my_sessions', view_args_conv={'event_id': 'confId'}))

_compat_bp.add_url_rule('!/sessionDisplay.py', 'session_modpython',
                        make_compat_redirect_func(_compat_bp, 'session',
                                                  view_args_conv={'confId': 'event_id',
                                                                  'sessionId': 'legacy_session_id'}))
