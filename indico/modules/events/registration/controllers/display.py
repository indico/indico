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

from flask import request, session, redirect

from indico.core.db import db
from indico.modules.events.registration.models.registration_forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.registration.util import (get_event_section_data, make_registration_form,
                                                     save_registration_to_session)
from indico.modules.events.registration.views import (WPDisplayRegistrationFormConference,
                                                      WPDisplayRegistrationFormMeeting,
                                                      WPDisplayRegistrationFormLecture)
from indico.modules.payment import event_settings
from indico.web.flask.util import url_for
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHRegistrationFormDisplayBase(RHConferenceBaseDisplay):

    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.event = self._conf

    @property
    def view_class(self):
        mapping = {
            'conference': WPDisplayRegistrationFormConference,
            'meeting': WPDisplayRegistrationFormMeeting,
            'simple_event': WPDisplayRegistrationFormLecture
        }
        return mapping[self.event.getType()]


class RHRegistrationFormList(RHRegistrationFormDisplayBase):
    """List of all registration forms in the event"""

    def _process(self):
        regforms = RegistrationForm.find_all(is_active=True, event_id=int(self.event.id))
        return self.view_class.render_template('display/regforms_list.html', self.event, regforms=regforms,
                                               event=self.event)


class RHRegistrationFormSubmit(RHRegistrationFormDisplayBase):
    """Submit a registration form"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.regform
        }
    }

    def _checkParams(self, params):
        RHRegistrationFormDisplayBase._checkParams(self, params)
        self.regform = RegistrationForm.find_one(id=request.view_args['reg_form_id'])

    def _process(self):
        form = make_registration_form(self.regform)()
        if form.validate_on_submit():
            self._save_registration(form.data)
            return redirect(url_for('.display_regforms_list', self.regform))
        return self.view_class.render_template('display/regform_display.html', self.event, event=self.event,
                                               sections=get_event_section_data(self.regform), regform=self.regform,
                                               currency=event_settings.get(self.event, 'currency'))

    def _save_registration(self, data):
        registration = Registration(user=session.user, registration_form=self.regform)
        db.session.add(registration)
        for form_item in self.regform.active_fields:
            value = data.get('field_{0}-{1}'.format(form_item.parent_id, form_item.id), None)
            form_item.wtf_field.save_data(registration, value)
        db.session.flush()
        save_registration_to_session(registration)
