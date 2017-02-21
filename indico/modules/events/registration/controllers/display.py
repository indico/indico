# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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
from uuid import UUID

from flask import request, session, redirect, flash, jsonify
from sqlalchemy.orm import subqueryload, contains_eager
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.db import db
from indico.modules.auth.util import redirect_to_login
from indico.modules.events.models.events import EventType
from indico.modules.events.registration import registration_settings
from indico.modules.events.registration.controllers import RegistrationEditMixin, RegistrationFormMixin
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.invitations import RegistrationInvitation, InvitationState
from indico.modules.events.registration.models.items import PersonalDataType
from indico.modules.events.registration.models.registrations import Registration, RegistrationState
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

    @property
    def view_class(self):
        mapping = {
            EventType.conference: WPDisplayRegistrationFormConference,
            EventType.meeting: WPDisplayRegistrationFormMeeting,
            EventType.lecture: WPDisplayRegistrationFormLecture
        }
        return mapping[self.event_new.type_]


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
        regforms = RegistrationForm.query.with_parent(self.event_new)
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
        return self.view_class.render_template('display/regform_list.html', self._conf, event=self.event_new,
                                               regforms=regforms)


class RHParticipantList(RHRegistrationFormDisplayBase):
    """List of all public registrations"""

    view_class = WPDisplayRegistrationParticipantList

    @staticmethod
    def _is_checkin_visible(reg):
        return reg.registration_form.publish_checkin_enabled and reg.checked_in

    def _merged_participant_list_table(self):
        def _process_registration(reg, column_names):
            personal_data = reg.get_personal_data()
            columns = [{'text': personal_data.get(column_name, '')} for column_name in column_names]
            return {'checked_in': self._is_checkin_visible(reg), 'columns': columns}

        def _deduplicate_reg_data(reg_data_iter):
            used = set()
            for reg_data in reg_data_iter:
                reg_data_hash = tuple(tuple(sorted(x.items())) for x in reg_data['columns'])
                if reg_data_hash not in used:
                    used.add(reg_data_hash)
                    yield reg_data

        column_names = registration_settings.get(self.event_new, 'participant_list_columns')
        headers = [PersonalDataType[column_name].get_title() for column_name in column_names]

        query = (Registration.query.with_parent(self.event_new)
                 .filter(Registration.state.in_([RegistrationState.complete, RegistrationState.unpaid]),
                         RegistrationForm.publish_registrations_enabled,
                         ~RegistrationForm.is_deleted,
                         ~Registration.is_deleted)
                 .join(Registration.registration_form)
                 .options(subqueryload('data').joinedload('field_data'),
                          contains_eager('registration_form')))
        registrations = sorted(_deduplicate_reg_data(_process_registration(reg, column_names) for reg in query),
                               key=lambda x: x['columns'])
        table = {'headers': headers,
                 'rows': registrations,
                 'show_checkin': any(registration['checked_in'] for registration in registrations)}
        return table

    def _participant_list_table(self, regform):
        def _process_registration(reg, column_ids, active_fields):
            data_by_field = reg.data_by_field

            def _content(column_id):
                if column_id in data_by_field:
                    return data_by_field[column_id].get_friendly_data(for_humans=True)
                elif column_id in active_fields and active_fields[column_id].personal_data_type is not None:
                    # some legacy registrations have no data in the firstname/lastname/email field
                    # so we need to get it from the registration object itself
                    return getattr(reg, active_fields[column_id].personal_data_type.column)
                else:
                    # no data available for the field
                    return ''

            columns = [{'text': _content(column_id)} for column_id in column_ids]
            return {'checked_in': self._is_checkin_visible(reg), 'columns': columns}

        active_fields = {field.id: field for field in regform.active_fields}
        column_ids = [column_id
                      for column_id in registration_settings.get_participant_list_columns(self.event_new, regform)
                      if column_id in active_fields]
        headers = [active_fields[column_id].title.title() for column_id in column_ids]
        active_registrations = sorted(regform.active_registrations, key=attrgetter('last_name', 'first_name', 'id'))
        registrations = [_process_registration(reg, column_ids, active_fields) for reg in active_registrations]
        table = {'headers': headers, 'rows': registrations, 'title': regform.title}
        table['show_checkin'] = any(registration['checked_in'] for registration in registrations)
        return table

    def _process(self):
        regforms = (self.event_new.registration_forms
                    .filter(RegistrationForm.publish_registrations_enabled,
                            ~RegistrationForm.is_deleted)
                    .options(subqueryload('registrations').subqueryload('data').joinedload('field_data'))
                    .all())
        if registration_settings.get(self.event_new, 'merge_registration_forms'):
            tables = [self._merged_participant_list_table()]
        else:
            tables = []
            regforms_dict = {regform.id: regform for regform in regforms if regform.publish_registrations_enabled}
            for form_id in registration_settings.get_participant_list_form_ids(self.event_new):
                try:
                    regform = regforms_dict.pop(form_id)
                except KeyError:
                    # The settings might reference forms that are not available
                    # anymore (publishing was disabled, etc.)
                    continue
                tables.append(self._participant_list_table(regform))
            # There might be forms that have not been sorted by the user yet
            tables += map(self._participant_list_table, regforms_dict.viewvalues())

        published = (RegistrationForm.query.with_parent(self.event_new)
                     .filter(RegistrationForm.publish_registrations_enabled)
                     .has_rows())
        num_participants = sum(len(table['rows']) for table in tables)

        return self.view_class.render_template(
            'display/participant_list.html',
            self._conf,
            regforms=regforms,
            tables=tables,
            published=published,
            num_participants=num_participants
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
        return self.view_class.render_template('display/regform_display.html', self._conf, event=self.event_new,
                                               regform=self.regform,
                                               sections=get_event_section_data(self.regform),
                                               payment_conditions=payment_event_settings.get(self.event_new,
                                                                                             'conditions'),
                                               payment_enabled=self.event_new.has_feature('payment'),
                                               user_data=user_data,
                                               invitation=self.invitation,
                                               registration=self.registration,
                                               management=False,
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
        return redirect(self.event_new.url)
