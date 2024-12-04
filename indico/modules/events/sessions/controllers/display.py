# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO
from itertools import groupby

from flask import render_template, request, session
from sqlalchemy.orm import joinedload, subqueryload
from werkzeug.exceptions import Forbidden

from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.events.sessions.ical import session_to_ical
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.util import get_sessions_for_user
from indico.modules.events.sessions.views import WPDisplayMySessionsConference, WPDisplaySession
from indico.modules.events.timetable.controllers.display import (RHTimetableExportPDF, TimetableExportConfig,
                                                                 TimetableExportProgramConfig)
from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.modules.events.timetable.util import (create_pdf, get_nested_timetable,
                                                  get_nested_timetable_location_conditions)
from indico.util.date_time import now_utc
from indico.web.flask.util import send_file
from indico.web.rh import allow_signed_url


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
                                               sess=sess, page_title=sess.title)


@allow_signed_url
class RHExportSessionToICAL(RHDisplaySessionBase):
    def _process(self):
        detailed = request.args.get('detail') == 'contributions'

        return send_file('session.ics', BytesIO(session_to_ical(self.session, session.user, detailed)),
                         'text/calendar')


class RHExportSessionTimetableToPDF(RHDisplaySessionBase, RHTimetableExportPDF):
    def _process(self):
        now = now_utc()
        css = render_template('events/timetable/pdf/timetable.css')
        event = self.event
        entries = [
            e for e in get_nested_timetable(event)
            if e.type == TimetableEntryType.SESSION_BLOCK and (
                e.id == self.session.id or (e.session_block and self.session.id == e.session_block.session.id)
            )
        ]
        days = {
            day: list(e) for day, e in groupby(
                entries, lambda e: e.start_dt.astimezone(self.event.tzinfo).date()
            )
        }
        config = TimetableExportConfig(
            show_title=True,
            show_affiliation=False,
            show_cover_page=False,
            show_toc=False,
            show_session_toc=True,
            show_abstract=False,
            dont_show_poster_abstract=False,
            show_contribs=False,
            show_length_contribs=False,
            show_breaks=False,
            new_page_per_session=False,
            show_session_description=False,
            print_date_close_to_sessions=False
        )

        show_siblings_location, show_children_location = get_nested_timetable_location_conditions(entries)
        program_config = TimetableExportProgramConfig(
            show_siblings_location=show_siblings_location,
            show_children_location=show_children_location
        )

        html = render_template('events/timetable/pdf/timetable.html', event=self.event,
                                days=days, now=now, config=config, program_config=program_config)

        return send_file('timetable.pdf', create_pdf(html, css, self.event), 'application/pdf')
