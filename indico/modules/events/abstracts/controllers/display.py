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

from flask import request, session, flash
from werkzeug.exceptions import Forbidden

from indico.modules.events.abstracts.controllers.base import RHAbstractsBase
from indico.modules.events.abstracts.operations import create_abstract
from indico.modules.events.abstracts.util import get_user_abstracts, make_abstract_form
from indico.modules.events.abstracts.views import WPDisplayAbstracts
from indico.modules.events.util import get_field_values
from indico.util.i18n import _
from indico.web.flask.util import send_file, url_for
from indico.web.util import jsonify_data, jsonify_form
from MaKaC.PDFinterface.conference import AbstractsToPDF


class RHCallForAbstracts(RHAbstractsBase):
    """Show the main CFA page"""

    def _process(self):
        abstracts = get_user_abstracts(self.event_new, session.user) if session.user else []
        return WPDisplayAbstracts.render_template('display/call_for_abstracts.html', self._conf,
                                                  event=self.event_new, abstracts=abstracts)


class RHMyAbstractsExportPDF(RHAbstractsBase):
    """Export the list of the user's abstracts as PDF"""

    def _checkProtection(self):
        if not session.user:
            raise Forbidden
        RHAbstractsBase._checkProtection(self)

    def _process(self):
        pdf = AbstractsToPDF(self.event_new, get_user_abstracts(self.event_new, session.user))
        return send_file('my-abstracts.pdf', pdf.generate(), 'application/pdf')


class RHSubmitAbstract(RHAbstractsBase):
    """Submit a new abstract."""

    def _checkProtection(self):
        if not session.user or not self.event_new.cfa.can_submit_abstracts(session.user):
            raise Forbidden
        RHAbstractsBase._checkProtection(self)

    def _process(self):
        abstract_form_class = make_abstract_form(self.event_new)
        form = abstract_form_class(event=self.event_new)
        if form.validate_on_submit():
            abstract = create_abstract(self.event_new, *get_field_values(form.data), send_notifications=True)
            flash(_("Your abstract '{}' has been successfully submitted. It is registered with the number "
                    "#{}. You will be notified by email with the submission details.")
                  .format(abstract.title, abstract.friendly_id), 'success')
            return jsonify_data(flash=False, redirect=url_for('.call_for_abstracts', self.event_new))
        return jsonify_form(form, submit=_("Submit"), back=_("Cancel"),
                            form_header_kwargs={'action': request.relative_url})
