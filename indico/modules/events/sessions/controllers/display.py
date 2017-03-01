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

from io import BytesIO

from flask import session, request
from sqlalchemy.orm import joinedload, subqueryload
from werkzeug.exceptions import Forbidden

from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.util import (get_sessions_for_user, get_session_ical_file,
                                                 get_session_timetable_pdf)
from indico.modules.events.sessions.views import WPDisplaySession, WPDisplayMySessionsConference
from indico.modules.events.util import get_base_ical_parameters
from indico.web.flask.util import send_file
from indico.legacy.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHDisplaySessionList(RHConferenceBaseDisplay):
    def _checkProtection(self):
        if not session.user:
            raise Forbidden
        RHConferenceBaseDisplay._checkProtection(self)

    def _process(self):
        sessions = get_sessions_for_user(self.event_new, session.user)
        return WPDisplayMySessionsConference.render_template('display/session_list.html', self._conf,
                                                             event=self.event_new, sessions=sessions)


class RHDisplaySessionBase(RHConferenceBaseDisplay):
    normalize_url_spec = {
        'locators': {
            lambda self: self.session
        }
    }

    def _checkProtection(self):
        if not self.session.can_access(session.user):
            raise Forbidden

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.session = Session.get_one(request.view_args['session_id'], is_deleted=False)


class RHDisplaySession(RHDisplaySessionBase):
    view_class = WPDisplaySession

    def _process(self):
        ical_params = get_base_ical_parameters(session.user, 'sessions',
                                               '/export/event/{0}/session/{1}.ics'.format(self.event_new.id,
                                                                                          self.session.id))
        contributions_strategy = subqueryload('contributions')
        _contrib_tte_strategy = contributions_strategy.joinedload('timetable_entry')
        _contrib_tte_strategy.lazyload('*')
        contributions_strategy.joinedload('person_links')
        blocks_strategy = joinedload('blocks')
        blocks_strategy.joinedload('person_links')
        _block_tte_strategy = blocks_strategy.joinedload('timetable_entry')
        _block_tte_strategy.lazyload('*')
        _block_tte_strategy.joinedload('children')
        sess = (Session.query
                .filter_by(id=self.session.id)
                .options(contributions_strategy, blocks_strategy)
                .one())
        return self.view_class.render_template('display/session_display.html', self._conf, sess=sess,
                                               event=self.event_new, **ical_params)


class RHExportSessionToICAL(RHDisplaySessionBase):
    def _process(self):
        return send_file('session.ics', get_session_ical_file(self.session), 'text/calendar')


class RHExportSessionTimetableToPDF(RHDisplaySessionBase):
    def _process(self):
        pdf = get_session_timetable_pdf(self.session)
        return send_file('session-timetable.pdf', BytesIO(pdf.getPDFBin()), 'application/pdf')
