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

from flask import request, session, redirect, flash, jsonify
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.db import db
from indico.modules.auth.util import redirect_to_login
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers import RegistrationFormMixin
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.items import PersonalDataType, RegistrationFormItemType
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.registration.util import (get_event_section_data, make_registration_form)
from indico.modules.events.registration.views import (WPDisplayRegistrationFormConference,
                                                      WPDisplayRegistrationFormMeeting,
                                                      WPDisplayRegistrationFormLecture)
from indico.modules.payment import event_settings
from indico.modules.users.util import get_user_by_email
from indico.util.i18n import _
from indico.web.flask.util import url_for
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


def _can_redirect_to_single_regform(regforms):
    user = session.user
    return (len(regforms) == 1 and regforms[0].can_submit(user) and
            (not user or not regforms[0].get_registration(user=user)))


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


class RHRegistrationFormBase(RHRegistrationFormDisplayBase, RegistrationFormMixin):
    def _checkParams(self, params):
        RHRegistrationFormDisplayBase._checkParams(self, params)
        RegistrationFormMixin._checkParams(self)


class RHRegistrationFormRegistrationBase(RHRegistrationFormBase):
    """Base for RHs handling individual registrations"""

    def _checkParams(self, params):
        RHRegistrationFormBase._checkParams(self, params)
        self.token = request.args.get('token')
        if self.token:
            self.registration = self.regform.get_registration(uuid=self.token)
            if not self.registration:
                raise NotFound
        else:
            self.registration = self.regform.get_registration(user=session.user) if session.user else None


class RHRegistrationFormList(RHRegistrationFormDisplayBase):
    """List of all registration forms in the event"""

    def _process(self):
        regforms = RegistrationForm.find_all(RegistrationForm.is_visible, event_id=int(self.event.id))
        if _can_redirect_to_single_regform(regforms):
            return redirect(url_for('.display_regform_summary', regforms[0]))
        return self.view_class.render_template('display/regform_list.html', self.event,
                                               event=self.event, regforms=regforms)


class RHRegistrationFormSummary(RHRegistrationFormRegistrationBase):
    """Displays user summary for a registration form"""

    def _process(self):
        return self.view_class.render_template('display/regform_summary.html', self.event,
                                               event=self.event, regform=self.regform, registration=self.registration,
                                               payment_enabled=event_settings.get(self.event, 'enabled'),
                                               payment_conditions=bool(event_settings.get(self.event, 'conditions')))


class RHRegistrationFormCheckEmail(RHRegistrationFormBase):
    """Checks how an email will affect the registration"""

    def _process(self):
        email = request.args['email'].lower().strip()
        if self.regform.get_registration(email=email):
            return jsonify(email_used=True)
        user = get_user_by_email(email)
        if user:
            return jsonify(email_used=False, user=user.full_name, self=(user == session.user))
        else:
            return jsonify(email_used=False, user=None)


class RHRegistrationFormSubmit(RHRegistrationFormBase):
    """Submit a registration form"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.regform
        }
    }

    def _checkProtection(self):
        RHRegistrationFormBase._checkProtection(self)
        if self.regform.require_user and not session.user:
            raise Forbidden(response=redirect_to_login(reason=_('You are trying to register with a form '
                                                                'that requires you to be logged in')))

    def _checkParams(self, params):
        RHRegistrationFormBase._checkParams(self, params)
        if not self.regform.is_active:
            flash(_('This registration form is not active'), 'error')
            return redirect(url_for('.display_regform_list', self.event))
        elif session.user and self.regform.get_registration(user=session.user):
            flash(_('You have already registered with this form'), 'error')
            return redirect(url_for('.display_regform_list', self.event))
        elif self.regform.limit_reached:
            flash(_('The maximum number of registrations has been reached'), 'error')
            return redirect(url_for('.display_regform_list', self.event))

    def _process(self):
        form = make_registration_form(self.regform)()
        if form.validate_on_submit():
            registration = self._save_registration(form.data)
            return redirect(url_for('.display_regform_summary', registration.locator.registrant))
        elif form.is_submitted():
            # not very pretty but usually this never happens thanks to client-side validation
            for error in form.error_list:
                flash(error, 'error')
        user_data = {t.name: getattr(session.user, t.name) if session.user else '' for t in PersonalDataType}
        return self.view_class.render_template('display/regform_display.html', self.event, event=self.event,
                                               sections=get_event_section_data(self.regform), regform=self.regform,
                                               currency=event_settings.get(self.event, 'currency'),
                                               user_data=user_data)

    def _save_registration(self, data):
        registration = Registration(registration_form=self.regform, user=get_user_by_email(data['email']))
        for form_item in self.regform.active_fields:
            if form_item.parent.is_manager_only:
                value = form_item.field_impl.default_value
            else:
                value = data.get(form_item.html_field_name)
            form_item.field_impl.save_data(registration, value)
            if form_item.type == RegistrationFormItemType.field_pd and form_item.personal_data_type.column:
                setattr(registration, form_item.personal_data_type.column, value)
        db.session.flush()
        logger.info('New registration %s by %s', registration, session.user)
        return registration
