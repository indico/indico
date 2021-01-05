# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from io import BytesIO

from flask import request, session
from sqlalchemy.orm import joinedload, subqueryload
from werkzeug.exceptions import Forbidden

from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.util import get_session_ical_file, get_session_timetable_pdf, get_sessions_for_user
from indico.modules.events.sessions.views import WPDisplayMySessionsConference, WPDisplaySession
from indico.modules.events.util import get_base_ical_parameters
from indico.web.flask.util import send_file


class RHDisplaySessionList(RHDisplayEventBase):
    def _check_access(self):
        if not session.user:
            raise Forbidden
        RHDisplayEventBase._check_access(self)

    def _process(self):
        sessions = get_sessions_for_user(self.event, session.user)
        return WPDisplayMySessionsConference.render_template('display/session_list.html', self.event, sessions=sessions)


class RHDisplaySessionBase(RHDisplayEventBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.session
        }
    }

    def _check_access(self):
        if not self.session.can_access(session.user):
            raise Forbidden

    def _process_args(self):
        RHDisplayEventBase._process_args(self)
        self.session = Session.get_or_404(request.view_args['session_id'], is_deleted=False)


class RHDisplaySession(RHDisplaySessionBase):
    view_class = WPDisplaySession

    def _process(self):
        ical_params = get_base_ical_parameters(session.user, 'sessions',
                                               '/export/event/{0}/session/{1}.ics'.format(self.event.id,
                                                                                          self.session.id))
        contributions_strategy = subqueryload('contributions')
        contributions_strategy.joinedload('track')
        _contrib_tte_strategy = contributions_strategy.joinedload('timetable_entry')
        _contrib_tte_strategy.lazyload('*')
        contributions_strategy.joinedload('person_links')
        contributions_strategy.subqueryload('references')
        blocks_strategy = joinedload('blocks')
        blocks_strategy.joinedload('person_links')
        _block_tte_strategy = blocks_strategy.joinedload('timetable_entry')
        _block_tte_strategy.lazyload('*')
        _block_tte_strategy.joinedload('children')
        sess = (Session.query
                .filter_by(id=self.session.id)
                .options(contributions_strategy, blocks_strategy)
                .one())
        return self.view_class.render_template('display/session_display.html', self.event,
                                               sess=sess, page_title=sess.title, **ical_params)


class RHExportSessionToICAL(RHDisplaySessionBase):
    def _process(self):
        return send_file('session.ics', get_session_ical_file(self.session), 'text/calendar')


class RHExportSessionTimetableToPDF(RHDisplaySessionBase):
    def _process(self):
        pdf = get_session_timetable_pdf(self.session)
        return send_file('session-timetable.pdf', BytesIO(pdf.getPDFBin()), 'application/pdf')
