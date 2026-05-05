# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO

import qrcode
from flask import jsonify, redirect, request, session
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers.pil import SquareModuleDrawer
from webargs import fields

from indico.modules.events.controllers.base import RHDisplayEventBase, RHEventBase
from indico.modules.events.ical import CalendarScope, event_to_ical, events_to_ical
from indico.modules.events.layout.views import WPPage
from indico.modules.events.management.settings import privacy_settings
from indico.modules.events.models.events import EventType
from indico.modules.events.settings import autolinker_settings
from indico.modules.events.util import get_theme
from indico.modules.events.views import WPConferenceDisplay, WPConferencePrivacyDisplay, WPSimpleEventDisplay
from indico.web.args import use_kwargs
from indico.web.flask.util import send_file, url_for
from indico.web.rh import RHProtected, allow_signed_url


@allow_signed_url
class RHExportEventICAL(RHDisplayEventBase):
    @use_kwargs({
        'scope': fields.Enum(CalendarScope, load_default=None),
        'detail': fields.String(load_default=None),
        'series': fields.Boolean(load_default=False)  # Export the full event series
    }, location='query')
    def _process(self, scope, detail, series):
        if not scope and detail == 'contributions':
            scope = CalendarScope.contribution
        if not series:
            event_ical = event_to_ical(self.event, session.user, scope)
            return send_file('event.ics', BytesIO(event_ical), 'text/calendar')
        else:
            events_ical = events_to_ical(self.event.series.events, session.user, scope)
            return send_file('event-series.ics', BytesIO(events_ical), 'text/calendar')


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
            elif (
                not self.force_overview and
                self.event.default_page and
                self.event.default_page.menu_entry.can_access(session.user)
            ):
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


class RHDisplayPrivacyPolicy(RHDisplayEventBase):
    """Display event privacy policy."""

    view_class = WPConferencePrivacyDisplay

    def _process(self):
        return self.view_class.render_template(
            'privacy_policy.html' if request.is_xhr else 'privacy.html',
            self.event,
            privacy_info=privacy_settings.get_all(self.event)
        )


class RHAutoLinkerRules(RHProtected):
    """Get auto-linker configuration."""

    def _process(self):
        return jsonify(autolinker_settings.get_all())


class RHTQRCodeImage(RHDisplayEventBase):
    """Display QRCode for event URL."""

    def _process(self):
        # QRCode (Version 6 with error correction L can contain up to 106 bytes)
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=15, border=4)

        print('--------------------')
        print(self.event.url)
        print(self.event.external_url)
        print(self.event.short_url)
        print(self.event.short_external_url)
        print('--------------------')

        qr.add_data(self.event.external_url)  # short_external_url
        qr.make(fit=True)

        qr_img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=SquareModuleDrawer(),
            embeded_image_ratio=0.25,
            color_mask=SolidFillColorMask(back_color=(255, 255, 255), front_color=(0, 0, 0)),
            # embeded_image_path=f'{config.IMAGES_BASE_URL}/logo_indico_small_white_bg.png',
             embeded_image_path='indico/web/static/images/logo_indico_small_white_bg.png'
        )

        output = BytesIO()
        qr_img.save(output)
        output.seek(0)

        return send_file('qrcode.png', output, 'image/png')
