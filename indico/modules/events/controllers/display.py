# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO

from flask import jsonify, redirect, request, session

from indico.legacy.common.output import outputGenerator
from indico.legacy.common.xmlGen import XMLGen
from indico.modules.events.controllers.base import RHDisplayEventBase, RHEventBase
from indico.modules.events.ical import event_to_ical
from indico.modules.events.layout.views import WPPage
from indico.modules.events.models.events import EventType
from indico.modules.events.util import get_theme
from indico.modules.events.views import WPConferenceDisplay, WPSimpleEventDisplay
from indico.web.flask.util import send_file, url_for
from indico.web.rh import allow_signed_url


@allow_signed_url
class RHExportEventICAL(RHDisplayEventBase):
    def _process(self):
        detailed = request.args.get('detail') == 'contributions'
        event_ical = event_to_ical(self.event, session.user, detailed)
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


class RHEventMarcXML(RHDisplayEventBase):
    def _process(self):
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(session.user, xmlgen)
        xmlgen.openTag('marc:record', [
            ['xmlns:marc', 'http://www.loc.gov/MARC21/slim'],
            ['xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance'],
            ['xsi:schemaLocation',
             'http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd']
        ])
        outgen.confToXMLMarc21(self.event)
        xmlgen.closeTag('marc:record')
        return send_file(f'event-{self.event.id}.marc.xml', BytesIO(xmlgen.getXml().encode()), 'application/xml')
