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

from uuid import UUID

from flask import request, session, redirect, flash, jsonify
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.db import db
from indico.modules.auth.util import redirect_to_login
from indico.modules.events.registration.controllers import RegistrationEditMixin, RegistrationFormMixin
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.invitations import RegistrationInvitation, InvitationState
from indico.modules.events.registration.models.items import PersonalDataType
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.registration.util import (get_event_section_data, make_registration_form,
                                                     create_registration, check_registration_email, get_title_uuid)
from indico.modules.events.registration.views import (WPDisplayRegistrationFormConference,
                                                      WPDisplayRegistrationFormMeeting,
                                                      WPDisplayRegistrationFormLecture,
                                                      WPDisplayRegistrationParticipantList)
from indico.modules.events.payment import event_settings as payment_event_settings
from indico.util.i18n import _
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


class RHRegistrationFormBase(RegistrationFormMixin, RHRegistrationFormDisplayBase):
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
        regforms = self.event_new.registration_forms.filter(~RegistrationForm.is_deleted)
        if session.user:
            criteria = db.or_(
                RegistrationForm.is_scheduled,
                RegistrationForm.registrations.any((Registration.user == session.user) & Registration.is_active),
            )
        else:
            criteria = RegistrationForm.is_scheduled
        regforms = regforms.filter(criteria).order_by(db.func.lower(RegistrationForm.title)).all()
        if len(regforms) == 1:
            return redirect(url_for('.display_regform', regforms[0]))
        return self.view_class.render_template('display/regform_list.html', self.event, event=self.event,
                                               regforms=regforms)


class RHParticipantList(RHRegistrationFormDisplayBase):
    """List of all public registrations"""

    view_class = WPDisplayRegistrationParticipantList

    def _process(self):
        regforms = RegistrationForm.find_all(RegistrationForm.publish_registrations_enabled,
                                             event_id=int(self.event.id))
        query = (Registration
                 .find(Registration.event_id == self.event.id,
                       RegistrationForm.publish_registrations_enabled,
                       ~RegistrationForm.is_deleted,
                       ~Registration.is_deleted,
                       _join=Registration.registration_form)
                 .order_by(db.func.lower(Registration.last_name), db.func.lower(Registration.first_name)))
        registrations = [(reg.get_full_name(), reg.get_personal_data()) for reg in query]
        enabled_pd_fields = {field.personal_data_type for reg in regforms for field in reg.active_fields}
        affiliation_enabled = PersonalDataType.affiliation in enabled_pd_fields
        position_enabled = PersonalDataType.position in enabled_pd_fields
        published = bool(RegistrationForm.find(RegistrationForm.publish_registrations_enabled,
                         RegistrationForm.event_id == int(self.event.id)).count())
        return self.view_class.render_template(
            'display/participant_list.html',
            self.event,
            event=self.event,
            regforms=regforms,
            show_affiliation=affiliation_enabled and any(pd.get('affiliation') for reg, pd in registrations),
            show_position=position_enabled and any(pd.get('position') for reg, pd in registrations),
            registrations=registrations,
            published=published
        )


class InvitationMixin:
    """Mixin for RHs that accept an invitation token"""

    def _checkParams(self):
        self.invitation = None
        try:
            token = request.args['invitation']
        except KeyError:
            return
        try:
            UUID(hex=token)
        except ValueError:
            flash(_("Your invitation code is not valid."), 'warning')
            return
        self.invitation = RegistrationInvitation.find(uuid=token).with_parent(self.regform).first()
        if self.invitation is None:
            flash(_("This invitation does not exist or has been withdrawn."), 'warning')


class RHRegistrationFormCheckEmail(RHRegistrationFormBase):
    """Checks how an email will affect the registration"""

    def _process(self):
        email = request.args['email'].lower().strip()
        update = request.args.get('update')
        management = request.args.get('management') == '1'

        if update:
            existing = self.regform.get_registration(uuid=update)
            return jsonify(check_registration_email(self.regform, email, existing, management=management))
        else:
            return jsonify(check_registration_email(self.regform, email, management=management))


class RHRegistrationForm(InvitationMixin, RHRegistrationFormRegistrationBase):
    """Display a registration form and registrations, and process submissions"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.regform
        }
    }

    def _checkProtection(self):
        RHRegistrationFormRegistrationBase._checkProtection(self)
        if self.regform.require_login and not session.user and request.method != 'GET':
            raise Forbidden(response=redirect_to_login(reason=_('You are trying to register with a form '
                                                                'that requires you to be logged in')))

    def _checkParams(self, params):
        RHRegistrationFormRegistrationBase._checkParams(self, params)
        InvitationMixin._checkParams(self)
        if self.invitation and self.invitation.state == InvitationState.accepted and self.invitation.registration:
            return redirect(url_for('.display_regform', self.invitation.registration.locator.registrant))

    def _process(self):
        form = make_registration_form(self.regform)()
        if form.validate_on_submit():
            registration = create_registration(self.regform, form.data, self.invitation)
            return redirect(url_for('.display_regform', registration.locator.registrant))
        elif form.is_submitted():
            # not very pretty but usually this never happens thanks to client-side validation
            for error in form.error_list:
                flash(error, 'error')

        user_data = {t.name: getattr(session.user, t.name, None) if session.user else '' for t in PersonalDataType}
        if self.invitation:
            user_data.update((attr, getattr(self.invitation, attr)) for attr in ('first_name', 'last_name', 'email'))
        user_data['title'] = get_title_uuid(self.regform, user_data['title'])
        return self.view_class.render_template('display/regform_display.html', self.event, event=self.event,
                                               sections=get_event_section_data(self.regform), regform=self.regform,
                                               payment_conditions=payment_event_settings.get(self.event, 'conditions'),
                                               payment_enabled=self.event.has_feature('payment'),
                                               user_data=user_data, invitation=self.invitation,
                                               registration=self.registration, management=False,
                                               login_required=self.regform.require_login and not session.user)


class RHRegistrationDisplayEdit(RegistrationEditMixin, RHRegistrationFormRegistrationBase):
    """Submit a registration form"""

    template_file = 'display/registration_modify.html'
    management = False

    def _checkParams(self, params):
        RHRegistrationFormRegistrationBase._checkParams(self, params)
        if self.registration is None:
            if session.user:
                flash(_("We could not find a registration for you.  If have already registered, please use the "
                        "direct access link from the email you received after registering."), 'warning')
            else:
                flash(_("We could not find a registration for you.  If have already registered, please use the "
                        "direct access link from the email you received after registering or log in to your Indico "
                        "account."), 'warning')
            return redirect(url_for('.display_regform', self.regform))

    @property
    def success_url(self):
        return url_for('.display_regform', self.registration.locator.registrant)


class RHRegistrationFormDeclineInvitation(InvitationMixin, RHRegistrationFormBase):
    """Decline an invitation to register"""

    def _checkParams(self, params):
        RHRegistrationFormBase._checkParams(self, params)
        InvitationMixin._checkParams(self)

    def _process(self):
        if self.invitation.state == InvitationState.pending:
            self.invitation.state = InvitationState.declined
            flash(_("You declined the invitation to register."))
        return redirect(url_for('event.conferenceDisplay', self.event))
