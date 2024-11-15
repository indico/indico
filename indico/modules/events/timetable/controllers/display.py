# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from dataclasses import dataclass
from io import BytesIO

from flask import jsonify, render_template, request, session
from marshmallow import fields
from weasyprint import CSS, HTML
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.db import db
from indico.modules.events.contributions import contribution_settings
from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.events.layout import layout_settings
from indico.modules.events.timetable.forms import TimetablePDFExportForm
from indico.modules.events.timetable.legacy import TimetableSerializer
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.modules.events.timetable.util import (get_timetable_offline_pdf_generator, render_entry_info_balloon,
                                                  serialize_event_info)
from indico.modules.events.timetable.views import WPDisplayTimetable
from indico.modules.events.util import get_theme
from indico.modules.events.views import WPSimpleEventDisplay
from indico.modules.receipts.util import sandboxed_url_fetcher
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.args import use_kwargs
from indico.web.flask.util import send_file, url_for
from indico.web.util import jsonify_data, jsonify_template


class RHTimetableProtectionBase(RHDisplayEventBase):
    def _check_access(self):
        RHDisplayEventBase._check_access(self)
        published = contribution_settings.get(self.event, 'published')
        if not published and not self.event.can_manage(session.user):
            raise NotFound(_('The contributions of this event have not been published yet'))


class RHTimetable(RHTimetableProtectionBase):
    view_class = WPDisplayTimetable
    view_class_simple = WPSimpleEventDisplay

    def _process_args(self):
        RHTimetableProtectionBase._process_args(self)
        self.timetable_layout = request.args.get('layout') or request.args.get('ttLyt')
        self.theme, self.theme_override = get_theme(self.event, request.args.get('view'))

    def _process(self):
        self.event.preload_all_acl_entries()
        if self.theme is None:
            event_info = serialize_event_info(self.event)
            timetable_data = TimetableSerializer(self.event).serialize_timetable(strip_empty_days=True)
            timetable_settings = layout_settings.get(self.event, 'timetable_theme_settings')
            return self.view_class.render_template('display.html', self.event, event_info=event_info,
                                                   timetable_data=timetable_data, timetable_settings=timetable_settings,
                                                   timetable_layout=self.timetable_layout,
                                                   published=contribution_settings.get(self.event, 'published'))
        else:
            return self.view_class_simple(self, self.event, self.theme, self.theme_override).display()


class RHTimetableEntryInfo(RHTimetableProtectionBase):
    """Display timetable entry info balloon."""

    def _process_args(self):
        RHTimetableProtectionBase._process_args(self)
        self.entry = self.event.timetable_entries.filter_by(id=request.view_args['entry_id']).first_or_404()

    def _check_access(self):
        if not self.entry.can_view(session.user):
            raise Forbidden

    def _process(self):
        html = render_entry_info_balloon(self.entry)
        return jsonify(html=html)


@dataclass(frozen=True)
class TimetableExportConfig:
    show_title: bool
    show_affiliation: bool
    show_cover_page: bool
    show_toc: bool
    show_session_toc: bool
    show_abstract: bool
    dont_show_poster_abstract: bool
    show_contribs: bool
    show_length_contribs: bool
    show_breaks: bool
    new_page_per_session: bool
    show_session_description: bool
    print_date_close_to_sessions: bool


class RHTimetableExportPDF(RHTimetableProtectionBase):
    @use_kwargs({'download': fields.Bool(load_default=False)}, location='query')
    def _process(self, download):
        form = TimetablePDFExportForm(formdata=request.args, csrf_enabled=False)

        if form.validate_on_submit():
            days = {}
            now = now_utc()
            css = render_template('events/timetable/pdf/timetable.css')

            for day in self.event.iter_days():
                entries = (self.event.timetable_entries
                           .filter(
                               db.cast(TimetableEntry.start_dt.astimezone(self.event.tzinfo), db.Date) == day,
                               TimetableEntry.parent_id.is_(None))
                           .order_by(TimetableEntry.start_dt))
                days[day] = entries

            config = TimetableExportConfig(
                show_title=form.other.data['showSpeakerTitle'],
                show_affiliation=form.other.data['showSpeakerAffiliation'],
                show_cover_page=form.document_settings.data['showCoverPage'],
                show_toc=form.document_settings.data['showTableContents'],
                show_session_toc=form.document_settings.data['showSessionTOC'],
                show_abstract=form.contribution_info.data['showAbstract'],
                dont_show_poster_abstract=form.contribution_info.data['dontShowPosterAbstract'],
                show_contribs=form.visible_entries.data['showContribsAtConfLevel'],
                show_length_contribs=form.contribution_info.data['showLengthContribs'],
                show_breaks=form.visible_entries.data['showBreaksAtConfLevel'],
                new_page_per_session=form.session_info.data['newPagePerSession'],
                show_session_description=form.session_info.data['showSessionDescription'],
                print_date_close_to_sessions=form.session_info.data['printDateCloseToSessions']
            )

            html = render_template('events/timetable/pdf/timetable.html', event=self.event,
                                   days=days, now=now, config=config)

            if download:
                return send_file('timetable.pdf', create_pdf(html, css, self.event), 'application/pdf')
            else:
                url = url_for(request.endpoint, **dict(request.view_args, download=True, **request.args.to_dict(False)))
                return jsonify_data(flash=False, redirect=url, redirect_no_loading=True)
        return jsonify_template('events/timetable/timetable_pdf_export.html', form=form,
                                back_url=url_for('.timetable', self.event))


class RHTimetableExportDefaultPDF(RHTimetableProtectionBase):
    def _process(self):
        pdf = get_timetable_offline_pdf_generator(self.event)
        return send_file('timetable.pdf', BytesIO(pdf.getPDFBin()), 'application/pdf')


def create_pdf(html, css, event) -> BytesIO:
    css_url_fetcher = sandboxed_url_fetcher(event)
    html_url_fetcher = sandboxed_url_fetcher(event, allow_event_images=True)
    css = CSS(string=css, url_fetcher=css_url_fetcher)
    documents = [
        HTML(string=html, url_fetcher=html_url_fetcher).render(stylesheets=(css,))
    ]
    all_pages = [p for doc in documents for p in doc.pages]

    f = BytesIO()
    documents[0].copy(all_pages).write_pdf(f)
    f.seek(0)

    return f
