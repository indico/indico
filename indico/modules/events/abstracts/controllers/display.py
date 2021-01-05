# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, request, session
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.config import config
from indico.core.errors import NoReportError
from indico.legacy.pdfinterface.latex import AbstractsToPDF
from indico.modules.events.abstracts.controllers.base import RHAbstractBase, RHAbstractsBase
from indico.modules.events.abstracts.models.abstracts import AbstractState
from indico.modules.events.abstracts.operations import create_abstract, update_abstract
from indico.modules.events.abstracts.util import get_user_abstracts, make_abstract_form
from indico.modules.events.abstracts.views import WPDisplayAbstracts, WPDisplayCallForAbstracts
from indico.modules.events.util import get_field_values
from indico.util.i18n import _
from indico.web.flask.util import send_file, url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHCallForAbstracts(RHAbstractsBase):
    """Show the main CFA page."""

    def _process(self):
        abstracts = get_user_abstracts(self.event, session.user) if session.user else []
        return WPDisplayCallForAbstracts.render_template('display/call_for_abstracts.html', self.event,
                                                         abstracts=abstracts)


class RHMyAbstractsExportPDF(RHAbstractsBase):
    """Export the list of the user's abstracts as PDF."""

    def _check_access(self):
        if not session.user:
            raise Forbidden
        RHAbstractsBase._check_access(self)

    def _process(self):
        if not config.LATEX_ENABLED:
            raise NotFound
        pdf = AbstractsToPDF(self.event, get_user_abstracts(self.event, session.user))
        return send_file('my-abstracts.pdf', pdf.generate(), 'application/pdf')


class RHSubmitAbstract(RHAbstractsBase):
    """Submit a new abstract."""

    ALLOW_LOCKED = True

    def _check_access(self):
        cfa = self.event.cfa
        if session.user and not cfa.is_open and not cfa.can_submit_abstracts(session.user):
            raise NoReportError.wrap_exc(Forbidden(_('The Call for Abstracts is closed. '
                                                     'Please contact the event organizer for further assistance.')))
        elif not session.user or not cfa.can_submit_abstracts(session.user):
            raise Forbidden
        RHAbstractsBase._check_access(self)

    def _process(self):
        abstract_form_class = make_abstract_form(self.event, session.user, management=self.management)
        form = abstract_form_class(event=self.event)
        if form.validate_on_submit():
            abstract = create_abstract(self.event, *get_field_values(form.data), send_notifications=True)
            flash(_("Your abstract '{}' has been successfully submitted. It is registered with the number "
                    "#{}. You will be notified by email with the submission details.")
                  .format(abstract.title, abstract.friendly_id), 'success')
            return jsonify_data(flash=False, redirect=url_for('.call_for_abstracts', self.event))
        return jsonify_template('events/abstracts/display/submission.html', event=self.event, form=form)


class RHSubmitInvitedAbstract(RHAbstractBase):
    USE_ABSTRACT_UUID = True

    def _check_access(self):
        RHAbstractBase._check_access(self)
        if self.abstract.state != AbstractState.invited:
            raise Forbidden

    def _check_abstract_protection(self):
        token = request.view_args['uuid']
        return self.abstract.uuid == token

    def _create_form(self):
        form_user = session.user or self.abstract.submitter
        abstract_form_cls = make_abstract_form(self.event, form_user)
        custom_field_values = {'custom_{}'.format(x.contribution_field_id): x.data for x in self.abstract.field_values}
        form_defaults = FormDefaults(self.abstract, **custom_field_values)
        return abstract_form_cls(obj=form_defaults, event=self.event, abstract=self.abstract)

    def _process_GET(self):
        return WPDisplayAbstracts.render_template('invited_abstract.html', self.abstract.event, abstract=self.abstract,
                                                  form=self._create_form())

    def _process_POST(self):
        form = self._create_form()
        if form.validate_on_submit():
            fields, custom_fields = get_field_values(form.data)
            abstract_data = dict(fields, state=AbstractState.submitted, uuid=None)
            update_abstract(self.abstract, abstract_data, custom_fields)
            return jsonify_data(flash=False, redirect=url_for('.call_for_abstracts', self.event))
        return jsonify_form(form, form_header_kwargs={'action': url_for('.submit_invited_abstract',
                                                                        self.abstract.locator.token)})
