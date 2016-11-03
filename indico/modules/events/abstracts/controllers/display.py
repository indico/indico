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

from operator import attrgetter

from flask import session, flash, redirect, request
from werkzeug.exceptions import Forbidden

from indico.modules.events.abstracts.controllers.base import AbstractPageMixin
from indico.modules.events.abstracts.operations import create_abstract
from indico.modules.events.abstracts.util import get_user_abstracts, make_abstract_form
from indico.modules.events.abstracts.views import WPDisplayAbstracts, WPMyAbstracts, WPSubmitAbstract
from indico.modules.events.util import get_field_values
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.web.flask.util import send_file, url_for
from indico.web.util import jsonify_data
from MaKaC.PDFinterface.conference import AbstractToPDF, AbstractsToPDF
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHDisplayAbstractsBase(RHConferenceBaseDisplay):
    CSRF_ENABLED = True
    EVENT_FEATURE = 'abstracts'


class RHDisplayAbstract(AbstractPageMixin, RHDisplayAbstractsBase):
    management = False
    page_class = WPDisplayAbstracts

    def _checkParams(self, params):
        RHDisplayAbstractsBase._checkParams(self, params)
        AbstractPageMixin._checkParams(self)

    def _checkProtection(self):
        RHDisplayAbstractsBase._checkProtection(self)
        AbstractPageMixin._checkProtection(self)


class RHDisplayAbstractExportPDF(RHDisplayAbstract):
    def _process(self):
        pdf = AbstractToPDF(self.abstract)
        file_name = secure_filename('abstract-{}.pdf'.format(self.abstract.friendly_id), 'abstract.pdf')
        return send_file(file_name, pdf.generate(), 'application/pdf')


class RHMyAbstractsBase(RHDisplayAbstractsBase):
    """Base RH concerning the list of current user abstracts"""

    def _checkParams(self, params):
        RHDisplayAbstractsBase._checkParams(self, params)
        self.abstracts = get_user_abstracts(self.event_new, session.user)

    def _checkProtection(self):
        RHDisplayAbstractsBase._checkProtection(self)
        if not session.user:
            raise Forbidden


class RHMyAbstracts(RHMyAbstractsBase):
    """Display the list of current user abstracts"""

    def _process(self):
        return WPMyAbstracts.render_template('display/user_abstract_list.html', self._conf, event=self.event_new,
                                             abstracts=self.abstracts)


class RHMyAbstractsExportPDF(RHMyAbstractsBase):
    def _process(self):
        sorted_abstracts = sorted(self.abstracts, key=attrgetter('friendly_id'))
        pdf = AbstractsToPDF(self.event_new, sorted_abstracts)
        return send_file('my-abstracts.pdf', pdf.generate(), 'application/pdf')


class RHSubmitAbstract(RHDisplayAbstractsBase):
    def _process(self):
        if not self.event_new.cfa.can_submit_abstracts(session.user):
            return WPSubmitAbstract.render_template('display/submit_abstract.html', self._conf, event=self.event_new,
                                                    form=None)
        abstract_form_class = make_abstract_form(self.event_new)
        form = abstract_form_class(event=self.event_new)
        if form.validate_on_submit():
            data = form.data
            abstract = create_abstract(self.event_new, *get_field_values(data))
            flash(_("Your abstract with title '{}' has been successfully submitted. It is registered with the number "
                    "#{}. You will be notified by email with the submission details.")
                  .format(abstract.title, abstract.friendly_id), 'success')
            url = url_for('.my_abstracts', self.event_new)
            if request.is_xhr:
                return jsonify_data(flash=False, redirect=url)
            else:
                return redirect(url)
        return WPSubmitAbstract.render_template('display/submit_abstract.html', self._conf, event=self.event_new,
                                                form=form)
