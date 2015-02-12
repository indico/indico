# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import flash, redirect, request, session

from indico.core.errors import AccessError, NotFoundError
from indico.util.i18n import _
from indico.web.flask.util import url_for
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase

from indico.modules.agreements.forms import AgreementForm
from indico.modules.agreements.models.agreements import Agreement
from indico.modules.agreements.notifications import notify_agreement_required_reminder
from indico.modules.agreements.views import WPAgreementForm, WPAgreementManager
from indico.modules.agreements.util import get_agreement_definitions, send_new_agreements


class RHAgreementForm(RHConferenceBaseDisplay):
    """Agreement form page"""

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.agreement = Agreement.find_one(id=request.view_args['id'])

    def _checkSessionUser(self):
        if session.user is None:
            self._redirect(self._getLoginURL())
        if self.agreement.user != session.user:
            raise AccessError()

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        if self.agreement.uuid != request.view_args['uuid']:
            raise AccessError()
        if self.agreement.user:
            self._checkSessionUser()

    def _process(self):
        form = AgreementForm()
        if form.validate_on_submit() and self.agreement.pending:
            if form.agreed.data:
                self.agreement.accept()
            else:
                self.agreement.reject()
        html = self.agreement.render(form)
        return WPAgreementForm.render_string(html, self._conf)


class RHAgreementManager(RHConferenceModifBase):
    """Agreement manager page (admin)"""

    def _process(self):
        definitions = get_agreement_definitions().values()
        return WPAgreementManager.render_template('agreements/event_agreements.html', self._conf,
                                                  event=self._conf, definitions=definitions)


class RHAgreementManagerDetails(RHConferenceModifBase):
    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        definition_name = request.view_args['definition']
        self.definition = get_agreement_definitions().get(definition_name)
        if self.definition is None:
            raise NotFoundError("Agreement definition '{}' does not exist".format(definition_name))

    def _process(self):
        event = self._conf
        agreements = Agreement.find_all(event_id=event.getId(), type=self.definition.name)
        return WPAgreementManager.render_template('agreements/event_agreements_details.html', event,
                                                  event=event, definition=self.definition, agreements=agreements)


class RHAgreementManagerDetailsSendAll(RHAgreementManagerDetails):
    def _process(self):
        event = self._conf
        people = self.definition.get_people_not_notified(event)
        send_new_agreements(event=event, name=self.definition.name, people=people)
        return redirect(url_for('.event_agreements_details', event, self.definition))


class RHAgreementManagerDetailsRemindAll(RHAgreementManagerDetails):
    def _process(self):
        event = self._conf
        agreements = Agreement.find_all(Agreement.pending, event_id=event.getId(), type=self.definition.name)
        for agreement in agreements:
            notify_agreement_required_reminder(agreement)
        flash(_("Reminders sent"), 'success')
        return redirect(url_for('.event_agreements_details', event, self.definition))
