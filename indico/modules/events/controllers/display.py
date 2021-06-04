# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO

from flask import jsonify, redirect, request, session
from marshmallow_enum import EnumField
from webargs import fields

from indico.modules.events.controllers.base import RHDisplayEventBase, RHEventBase
from indico.modules.events.ical import CalendarScope, event_to_ical
from indico.modules.events.layout.views import WPPage
from indico.modules.events.models.events import EventType
from indico.modules.events.util import get_theme
from indico.modules.events.views import WPConferenceDisplay, WPSimpleEventDisplay
from indico.web.args import use_kwargs
from indico.web.flask.util import send_file, url_for
from indico.web.rh import allow_signed_url


@allow_signed_url
class RHExportEventICAL(RHDisplayEventBase):
    @use_kwargs({
        'scope': EnumField(CalendarScope, missing=None),
        'detail': fields.String(missing=None)
    }, location='query')
    def _process(self, scope, detail):
        if not scope and detail == 'contributions':
            scope = CalendarScope.contribution
        event_ical = event_to_ical(self.event, session.user, scope)
        return send_file('event.ics', BytesIO(event_ical), 'text/calendar')


class RHDisplayEvent(RHDisplayEventBase):
    """Display the main page of an event.

    For a conference this is either the overview page or the custom
    home page if one has been set.
    For a meeting/lecture the timetable is shown.
    """

    def _process_args(self):
        RHDisplayEventBase._process_args(self)
        self.force_overview = request.view_args.get('force_overview', False)
        self.theme_id, self.theme_override = get_theme(self.event, request.args.get('view'))

    def _process(self):
        if self.event.type_ == EventType.conference:
            if self.theme_override:
                return redirect(url_for('timetable.timetable', self.event, view=self.theme_id))
            elif self.event.default_page and not self.force_overview:
                return self._display_conference_page()
            else:
                return self._display_conference()
        else:
            return self._display_simple()

    def _display_conference_page(self):
        """Display the custom conference home page."""
        return WPPage.render_template('page.html', self.event, page=self.event.default_page)

    def _display_conference(self):
        """Display the conference overview page."""
        return WPConferenceDisplay(self, self.event).display()

    def _display_simple(self):
        """Display a simple single-page event (meeting/lecture)."""
        return WPSimpleEventDisplay(self, self.event, self.theme_id, self.theme_override).display()


class RHEventAccessKey(RHEventBase):
    def _process(self):
        self.event.set_session_access_key(request.form['access_key'])
        return jsonify(valid=self.event.check_access_key())
