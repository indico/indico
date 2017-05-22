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

from flask import jsonify, request, session

from indico.legacy.pdfinterface.conference import SimplifiedTimeTablePlain, TimetablePDFFormat, TimeTablePlain
from indico.legacy.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from indico.modules.events.timetable.forms import TimetablePDFExportForm
from indico.modules.events.timetable.legacy import TimetableSerializer
from indico.modules.events.timetable.util import (get_timetable_offline_pdf_generator, render_entry_info_balloon,
                                                  serialize_event_info)
from indico.modules.events.timetable.views import WPDisplayTimetable
from indico.modules.events.util import get_theme
from indico.modules.events.views import WPSimpleEventDisplay
from indico.web.flask.util import send_file, url_for
from indico.web.util import jsonify_data, jsonify_template


class RHTimetable(RHConferenceBaseDisplay):
    view_class = WPDisplayTimetable
    view_class_simple = WPSimpleEventDisplay

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.timetable_layout = request.args.get('layout') or request.args.get('ttLyt')
        self.theme, self.theme_override = get_theme(self.event_new, request.args.get('view'))

    def _process(self):
        self.event_new.preload_all_acl_entries()
        if self.theme is None:
            event_info = serialize_event_info(self.event_new)
            timetable_data = TimetableSerializer().serialize_timetable(self.event_new, strip_empty_days=True)
            return self.view_class.render_template('display.html', self._conf, event_info=event_info,
                                                   timetable_data=timetable_data,
                                                   timetable_layout=self.timetable_layout)
        else:
            return self.view_class_simple(self, self._conf, self.theme, self.theme_override).display()


class RHTimetableEntryInfo(RHConferenceBaseDisplay):
    """Display timetable entry info balloon."""

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.entry = self.event_new.timetable_entries.filter_by(id=request.view_args['entry_id']).first_or_404()

    def _process(self):
        html = render_entry_info_balloon(self.entry)
        return jsonify(html=html)


class RHTimetableExportPDF(RHConferenceBaseDisplay):
    def _process(self):
        form = TimetablePDFExportForm(formdata=request.args, csrf_enabled=False)
        if form.validate_on_submit():
            form_data = form.data_for_format
            pdf_format = TimetablePDFFormat(form_data)
            if not form.advanced.data:
                pdf_class = SimplifiedTimeTablePlain
                additional_params = {}
            else:
                pdf_class = TimeTablePlain
                additional_params = {'firstPageNumber': form.firstPageNumber.data,
                                     'showSpeakerAffiliation': form_data['showSpeakerAffiliation'],
                                     'showSessionDescription': form_data['showSessionDescription']}
            if request.args.get('download') == '1':
                pdf = pdf_class(self.event_new, session.user, sortingCrit=None, ttPDFFormat=pdf_format,
                                pagesize=form.pagesize.data, fontsize=form.fontsize.data, **additional_params)
                return send_file('timetable.pdf', BytesIO(pdf.getPDFBin()), 'application/pdf')
            else:
                url = url_for(request.endpoint, **dict(request.view_args, download='1', **request.args.to_dict(False)))
                return jsonify_data(flash=False, redirect=url, redirect_no_loading=True)
        return jsonify_template('events/timetable/timetable_pdf_export.html', form=form,
                                back_url=url_for('.timetable', self.event_new))


class RHTimetableExportDefaultPDF(RHConferenceBaseDisplay):
    def _process(self):
        pdf = get_timetable_offline_pdf_generator(self.event_new)
        return send_file('timetable.pdf', BytesIO(pdf.getPDFBin()), 'application/pdf')
