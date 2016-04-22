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

from flask import jsonify, request, session

from indico.modules.events.timetable.forms import TimetablePDFExportForm
from indico.modules.events.timetable.legacy import TimetableSerializer
from indico.modules.events.timetable.views import WPDisplayTimetable
from indico.modules.events.timetable.util import (render_entry_info_balloon, serialize_event_info,
                                                  get_timetable_offline_pdf_generator)
from indico.web.flask.util import send_file, url_for
from MaKaC.PDFinterface.conference import TimeTablePlain, TimetablePDFFormat, SimplifiedTimeTablePlain
from MaKaC.webinterface.pages.conferences import WPTPLConferenceDisplay
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHTimetable(RHConferenceBaseDisplay):
    view_class = WPDisplayTimetable

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.layout = request.args.get('layout')
        if not self.layout:
            self.layout = request.args.get('ttLyt')

    def _process(self):
        if self.event_new.theme == 'static':
            event_info = serialize_event_info(self.event_new)
            timetable_data = TimetableSerializer().serialize_timetable(self.event_new)
            return self.view_class.render_template('display.html', self._conf, event_info=event_info,
                                                      timetable_data=timetable_data, timetable_layout=self.layout)
        else:
            page = WPTPLConferenceDisplay(self, self._conf, view=self.event_new.theme, type='meeting', params={})
            return page.display()


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
        form = TimetablePDFExportForm()
        if form.validate_on_submit():
            form_data = form.data_for_format
            pdf_format = TimetablePDFFormat(form_data)
            if not form.advanced.data:
                pdf_class = SimplifiedTimeTablePlain
                additional_params = {}
            else:
                pdf_class = TimeTablePlain
                additional_params = {'firstPageNumber': form.firstPageNumber.data,
                                     'showSpeakerAffiliation': form_data['showSpeakerAffiliation']}
            pdf = pdf_class(self.event_new, session.user, sortingCrit=None, ttPDFFormat=pdf_format,
                            pagesize=form.pagesize.data, fontsize=form.fontsize.data, **additional_params)
            return send_file('timetable.pdf', BytesIO(pdf.getPDFBin()), 'application/pdf')
        return WPDisplayTimetable.render_template('timetable_pdf_export.html', self._conf, form=form,
                                                  back_url=url_for('.timetable', self.event_new))


class RHTimetableExportDefaultPDF(RHConferenceBaseDisplay):
    def _process(self):
        pdf = get_timetable_offline_pdf_generator(self.event_new)
        return send_file('timetable.pdf', BytesIO(pdf.getPDFBin()), 'application/pdf')
