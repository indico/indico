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

from io import BytesIO

from flask import session, request
from pytz import timezone
from werkzeug.exceptions import Forbidden

from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.util import get_sessions_for_user, serialize_session_for_ical
from indico.modules.events.sessions.views import WPDisplayMySessionsConference
from indico.modules.events.timetable.legacy import TimetableSerializer, serialize_session
from indico.modules.events.util import get_base_ical_parameters
from indico.web.flask.util import send_file
from indico.web.http_api.metadata.serializer import Serializer
from MaKaC.common.fossilize import fossilize
from MaKaC.common.timezoneUtils import DisplayTZ
from MaKaC.fossils.conference import IConferenceEventInfoFossil
from MaKaC.PDFinterface.conference import TimeTablePlain, TimetablePDFFormat
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


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
    def _process(self):
        ical_params = get_base_ical_parameters(session.user, self.event_new, 'sessions')
        session_contribs = [c for c in self.session.contributions if not c.is_deleted]
        tz = timezone(DisplayTZ(session.user, self._conf).getDisplayTZ())
        timetable_data = TimetableSerializer().serialize_session(self.session)
        event_info = fossilize(self._conf, IConferenceEventInfoFossil, tz=self._conf.tz)
        event_info['isCFAEnabled'] = self._conf.getAbstractMgr().isActive()
        event_info['sessions'] = {sess.id: serialize_session(sess) for sess in self.event_new.sessions}
        return WPDisplayMySessionsConference.render_template('display/session_display.html', self._conf,
                                                             sess=self.session, event=self.event_new,
                                                             session_contribs=session_contribs, timezone=tz,
                                                             timetable_data=timetable_data, event_info=event_info,
                                                             timetable_layout=None,
                                                             **ical_params)


class RHExportSessionToICAL(RHDisplaySessionBase):
    def _process(self):
        data = {'results': serialize_session_for_ical(self.session)}
        serializer = Serializer.create('ics')
        return send_file('session.ics', BytesIO(serializer(data)), 'text/calendar')


class RHExportSessionTimetableToPDF(RHDisplaySessionBase):
    def _process(self):
        pdf_format = TimetablePDFFormat(params={'coverPage': False})
        pdf = TimeTablePlain(self._conf, session.user, showSessions=[self.session.id], showDays=[], sortingCrit=None,
                             ttPDFFormat=pdf_format, pagesize='A4', fontsize='normal', firstPageNumber=1,
                             showSpeakerAffiliation=False)
        return send_file('session-timetable.pdf', BytesIO(pdf.getPDFBin()), 'application/pdf')
