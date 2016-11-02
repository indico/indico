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

import os
from operator import attrgetter

from flask import render_template, redirect, request, session
from werkzeug.exceptions import Forbidden

from indico.modules.events.abstracts.forms import AbstractJudgmentForm, make_review_form
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.util import generate_spreadsheet_from_abstracts
from indico.modules.events.abstracts.views import WPDisplayAbstractsReviewing
from indico.modules.events.util import ZipGeneratorMixin
from indico.util.fs import secure_filename
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.web.flask.util import send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data
from MaKaC.PDFinterface.conference import ConfManagerAbstractsToPDF


def build_review_form(abstract, track):
    review_form_class = make_review_form(abstract.event_new)
    reviews_for_track = abstract.get_reviews(user=session.user, track=track)
    review_for_track = reviews_for_track[0] if reviews_for_track else None

    if review_for_track:
        answers = {'question_{}'.format(rating.question.id): rating.value
                   for rating in review_for_track.ratings}
        defaults = FormDefaults(obj=review_for_track, **answers)
    else:
        defaults = FormDefaults()

    return review_form_class(prefix="track-{}".format(track.id), obj=defaults, abstract=abstract)


def render_abstract_page(abstract, management=False):
    review_forms = {track.id: build_review_form(abstract, track)
                    for track in abstract.reviewed_for_tracks
                    if track.can_review_abstracts(session.user)}
    judgment_form = AbstractJudgmentForm(abstract=abstract)

    return render_template('events/abstracts/abstract.html', abstract=abstract, judgment_form=judgment_form,
                           review_forms=review_forms, management=management, no_javascript=True)


class AbstractMixin:
    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract
        }
    }

    def _checkParams(self):
        self.abstract = Abstract.get_one(request.view_args['abstract_id'], is_deleted=False)

    def _checkProtection(self):
        if not self.abstract.can_access(session.user):
            raise Forbidden


class AbstractPageMixin(AbstractMixin):
    """Display abstract page"""

    def _process(self):
        review_forms = {track.id: build_review_form(self.abstract, track)
                        for track in self.abstract.reviewed_for_tracks
                        if track.can_review_abstracts(session.user)}
        judgment_form = AbstractJudgmentForm(abstract=self.abstract)

        return self.page_class.render_template('abstract.html', self._conf, abstract=self.abstract,
                                               judgment_form=judgment_form, review_forms=review_forms,
                                               management=self.management)


class DisplayAbstractListMixin:
    """Display the list of abstracts"""

    view_class = None
    template = None

    def _process(self):
        if self.list_generator.static_link_used:
            return redirect(self.list_generator.get_list_url())
        return self._render_template(**self.list_generator.get_list_kwargs())

    def _render_template(self, **kwargs):
        return self.view_class.render_template(self.template, self._conf, event=self.event_new, **kwargs)


class CustomizeAbstractListMixin:
    """Filter options and columns to display for the abstract list of an event"""

    view_class = None

    def _process_GET(self):
        list_config = self.list_generator._get_config()
        return self.view_class.render_template('management/abstract_list_filter.html', self._conf,
                                               event=self.event_new, visible_items=list_config['items'],
                                               static_items=self.list_generator.static_items,
                                               extra_filters=self.list_generator.extra_filters,
                                               filters=list_config['filters'],
                                               reviewing_page=self.view_class == WPDisplayAbstractsReviewing)

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(flash=False, **self.list_generator.render_list())


class AbstractsExportPDFMixin:
    """Export list of abstracts to PDF"""

    def _process(self):
        sorted_abstracts = sorted(self.abstracts, key=attrgetter('friendly_id'))
        pdf = ConfManagerAbstractsToPDF(self.event_new, sorted_abstracts)
        return send_file('abstracts.pdf', pdf.generate(), 'application/pdf')


class _AbstractsExportBaseMixin:
    """Base class for all abstract list export classes"""

    def _generate_spreadsheet(self):
        export_config = self.list_generator.get_list_export_config()
        return generate_spreadsheet_from_abstracts(self.abstracts, export_config['static_item_ids'],
                                                   export_config['dynamic_items'])


class AbstractsExportCSV(_AbstractsExportBaseMixin):
    """Export list of abstracts to CSV"""

    def _process(self):
        return send_csv('abstracts.csv', *self._generate_spreadsheet())


class AbstractsExportExcel(_AbstractsExportBaseMixin):
    """Export list of abstracts to XLSX"""

    def _process(self):
        return send_xlsx('abstracts.xlsx', *self._generate_spreadsheet())


class AbstractsDownloadAttachmentsMixin(ZipGeneratorMixin):
    """Generate a ZIP file with attachment files for a given list of abstracts"""

    def _prepare_folder_structure(self, item):
        abstract_title = secure_filename('{}_{}'.format(item.abstract.title, unicode(item.abstract.id)), 'abstract')
        file_name = secure_filename('{}_{}'.format(unicode(item.id), item.filename), item.filename)
        return os.path.join(*self._adjust_path_length([abstract_title, file_name]))

    def _iter_items(self, abstracts):
        for abstract in abstracts:
            for f in abstract.files:
                yield f

    def _process(self):
        return self._generate_zip_file(self.abstracts, name_prefix='abstract-attachments',
                                       name_suffix=self.event_new.id)
