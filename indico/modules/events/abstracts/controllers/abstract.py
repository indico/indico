# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import flash, request, session
from sqlalchemy.orm import defaultload, joinedload

from indico.legacy.pdfinterface.conference import AbstractToPDF, ConfManagerAbstractToPDF
from indico.modules.events.abstracts.controllers.base import RHAbstractBase
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.abstracts.operations import update_abstract
from indico.modules.events.abstracts.util import make_abstract_form
from indico.modules.events.abstracts.views import WPDisplayAbstracts, WPManageAbstracts, render_abstract_page
from indico.modules.events.util import get_field_values
from indico.util.i18n import _
from indico.web.flask.util import send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHDisplayAbstract(RHAbstractBase):
    _abstract_query_options = (joinedload('reviewed_for_tracks'),
                               defaultload('reviews').joinedload('ratings').joinedload('question'))

    @property
    def view_class(self):
        return WPManageAbstracts if self.management else WPDisplayAbstracts

    def _process(self):
        return render_abstract_page(self.abstract, view_class=self.view_class, management=self.management)


class RHEditAbstract(RHAbstractBase):
    def _check_abstract_protection(self):
        return self.abstract.can_edit(session.user)

    def _process(self):
        abstract_form_class = make_abstract_form(self.event, session.user, management=self.management)
        custom_field_values = {'custom_{}'.format(x.contribution_field_id): x.data for x in self.abstract.field_values}
        defaults = FormDefaults(self.abstract, attachments=self.abstract.files, **custom_field_values)
        form = abstract_form_class(obj=defaults, abstract=self.abstract, event=self.event, management=self.management)
        if form.validate_on_submit():
            update_abstract(self.abstract, *get_field_values(form.data))
            flash(_("Abstract modified successfully"), 'success')
            return jsonify_data(flash=False)
        self.commit = False
        disabled_fields = ('submitted_for_tracks',) if form.track_field_disabled else ()
        return jsonify_form(form, disabled_fields=disabled_fields, form_header_kwargs={'action': request.relative_url})


class RHAbstractsDownloadAttachment(RHAbstractBase):
    """Download an attachment file belonging to an abstract."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract_file
        }
    }

    def _process_args(self):
        RHAbstractBase._process_args(self)
        self.abstract_file = AbstractFile.get_one(request.view_args['file_id'])

    def _process(self):
        return self.abstract_file.send()


class RHAbstractNotificationLog(RHAbstractBase):
    """Show the notifications sent for an abstract"""

    def _check_abstract_protection(self):
        return self.abstract.can_judge(session.user)

    def _process(self):
        return jsonify_template('events/abstracts/reviewing/notification_log.html', abstract=self.abstract)


class RHAbstractExportPDF(RHAbstractBase):
    def _process(self):
        pdf = AbstractToPDF(self.abstract)
        filename = 'abstract-{}.pdf'.format(self.abstract.friendly_id)
        return send_file(filename, pdf.generate(), 'application/pdf')


class RHAbstractExportFullPDF(RHAbstractBase):
    """Export an abstract as PDF (with review details)"""

    def _check_abstract_protection(self):
        return self.abstract.can_see_reviews(session.user)

    def _process(self):
        pdf = ConfManagerAbstractToPDF(self.abstract)
        filename = 'abstract-{}-reviews.pdf'.format(self.abstract.friendly_id)
        return send_file(filename, pdf.generate(), 'application/pdf')
