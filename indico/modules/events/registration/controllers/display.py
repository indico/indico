# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from operator import attrgetter
from uuid import UUID

from flask import flash, jsonify, redirect, request, session
from sqlalchemy.orm import contains_eager, subqueryload
from werkzeug.exceptions import Forbidden, NotFound

from indico.modules.auth.util import redirect_to_login
from indico.modules.events.controllers.base import RegistrationRequired, RHDisplayEventBase
from indico.modules.events.models.events import EventType
from indico.modules.events.payment import payment_event_settings
from indico.modules.events.registration import registration_settings
from indico.modules.events.registration.controllers import RegistrationEditMixin, RegistrationFormMixin
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.invitations import InvitationState, RegistrationInvitation
from indico.modules.events.registration.models.items import PersonalDataType
from indico.modules.events.registration.models.registrations import Registration, RegistrationState
from indico.modules.events.registration.util import (check_registration_email, create_registration, generate_ticket,
                                                     get_event_regforms_registrations, get_event_section_data,
                                                     get_title_uuid, make_registration_form)
from indico.modules.events.registration.views import (WPDisplayRegistrationFormConference,
                                                      WPDisplayRegistrationFormSimpleEvent,
                                                      WPDisplayRegistrationParticipantList)
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.web.flask.util import send_file, url_for


class RHRegistrationFormDisplayBase(RHDisplayEventBase):
    #: Whether to allow access for users who cannot access the event itself.
    ALLOW_PROTECTED_EVENT = False

    #: Whether the current request is accessing this page in restricted mode
    #: due to lack of access to the event.
    is_restricted_access = False

    @property
    def view_class(self):
        return (WPDisplayRegistrationFormConference
                if self.event.type_ == EventType.conference
                else WPDisplayRegistrationFormSimpleEvent)

    def _check_access(self):
        try:
            RHDisplayEventBase._check_access(self)
        except RegistrationRequired:
            self.is_restricted_access = True
            if not self.ALLOW_PROTECTED_EVENT or not self._check_restricted_event_access():
                raise Forbidden

    def _check_restricted_event_access(self):
        return True


class RHRegistrationFormBase(RegistrationFormMixin, RHRegistrationFormDisplayBase):
    def _process_args(self):
        RHRegistrationFormDisplayBase._process_args(self)
        RegistrationFormMixin._process_args(self)

    def _check_restricted_event_access(self):
        return self.regform.in_event_acls.filter_by(event_id=self.event.id).has_rows()


class RHRegistrationFormRegistrationBase(RHRegistrationFormBase):
    """Base for RHs handling individual registrations."""

    REGISTRATION_REQUIRED = True

    def _process_args(self):
        RHRegistrationFormBase._process_args(self)
        self.token = request.args.get('token')
        if self.token:
            self.registration = self.regform.get_registration(uuid=self.token)
            if not self.registration:
                raise NotFound
        else:
            self.registration = self.regform.get_registration(user=session.user) if session.user else None
        if self.REGISTRATION_REQUIRED and not self.registration:
            raise Forbidden


class RHRegistrationFormList(RHRegistrationFormDisplayBase):
    """List of all registration forms in the event."""

    ALLOW_PROTECTED_EVENT = True

    def _process(self):
        displayed_regforms, user_registrations = get_event_regforms_registrations(self.event, session.user,
                                                                                  only_in_acl=self.is_restricted_access)
        if len(displayed_regforms) == 1:
            return redirect(url_for('.display_regform', displayed_regforms[0]))
        return self.view_class.render_template('display/regform_list.html', self.event,
                                               regforms=displayed_regforms,
                                               user_registrations=user_registrations,
                                               is_restricted_access=self.is_restricted_access)


class RHParticipantList(RHRegistrationFormDisplayBase):
    """List of all public registrations."""

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

        column_names = registration_settings.get(self.event, 'participant_list_columns')
        headers = [PersonalDataType[column_name].get_title() for column_name in column_names]

        query = (Registration.query.with_parent(self.event)
                 .filter(Registration.is_publishable,
                         RegistrationForm.publish_registrations_enabled,
                         ~RegistrationForm.is_deleted,
                         ~Registration.is_deleted)
                 .join(Registration.registration_form)
                 .options(subqueryload('data').joinedload('field_data'),
                          contains_eager('registration_form')))
        registrations = sorted(_deduplicate_reg_data(_process_registration(reg, column_names) for reg in query),
                               key=lambda reg: tuple(x['text'].lower() for x in reg['columns']))
        return {'headers': headers,
                'rows': registrations,
                'show_checkin': any(registration['checked_in'] for registration in registrations)}

    def _participant_list_table(self, regform):
        def _process_registration(reg, column_ids, active_fields):
            data_by_field = reg.data_by_field

            def _content(column_id):
                if column_id in data_by_field:
                    return data_by_field[column_id].get_friendly_data(for_humans=True)
                elif (column_id in active_fields and active_fields[column_id].personal_data_type is not None and
                        active_fields[column_id].personal_data_type.column is not None):
                    # some legacy registrations have no data in the firstname/lastname/email field
                    # so we need to get it from the registration object itself
                    return getattr(reg, active_fields[column_id].personal_data_type.column)
                else:
                    # no data available for the field
                    return ''

            def _sort_key_date(column_id):
                data = data_by_field.get(column_id)
                if data and data.field_data.field.input_type == 'date':
                    return data.data
                else:
                    return None

            columns = [{'text': _content(column_id), 'sort_key': _sort_key_date(column_id)} for column_id in column_ids]
            return {'checked_in': self._is_checkin_visible(reg), 'columns': columns}

        active_fields = {field.id: field for field in regform.active_fields}
        column_ids = [column_id
                      for column_id in registration_settings.get_participant_list_columns(self.event, regform)
                      if column_id in active_fields]
        headers = [active_fields[column_id].title.title() for column_id in column_ids]
        active_registrations = sorted(regform.active_registrations, key=attrgetter('last_name', 'first_name', 'id'))
        registrations = [_process_registration(reg, column_ids, active_fields) for reg in active_registrations
                         if reg.is_publishable]
        return {'headers': headers,
                'rows': registrations,
                'title': regform.title,
                'show_checkin': any(registration['checked_in'] for registration in registrations)}

    def _process(self):
        regforms = (RegistrationForm.query.with_parent(self.event)
                    .filter(RegistrationForm.publish_registrations_enabled,
                            ~RegistrationForm.is_deleted)
                    .options(subqueryload('registrations').subqueryload('data').joinedload('field_data'))
                    .all())
        if registration_settings.get(self.event, 'merge_registration_forms'):
            tables = [self._merged_participant_list_table()]
        else:
            tables = []
            regforms_dict = {regform.id: regform for regform in regforms if regform.publish_registrations_enabled}
            for form_id in registration_settings.get_participant_list_form_ids(self.event):
                try:
                    regform = regforms_dict.pop(form_id)
                except KeyError:
                    # The settings might reference forms that are not available
                    # anymore (publishing was disabled, etc.)
                    continue
                tables.append(self._participant_list_table(regform))
            # There might be forms that have not been sorted by the user yet
            tables += map(self._participant_list_table, regforms_dict.viewvalues())

        published = (RegistrationForm.query.with_parent(self.event)
                     .filter(RegistrationForm.publish_registrations_enabled)
                     .has_rows())
        num_participants = sum(len(table['rows']) for table in tables)

        return self.view_class.render_template(
            'display/participant_list.html',
            self.event,
            regforms=regforms,
            tables=tables,
            published=published,
            num_participants=num_participants
        )


class InvitationMixin:
    """Mixin for RHs that accept an invitation token."""

    def _process_args(self):
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
    """Check how an email will affect the registration."""

    ALLOW_PROTECTED_EVENT = True

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
    """Display a registration form and registrations, and process submissions."""

    REGISTRATION_REQUIRED = False
    ALLOW_PROTECTED_EVENT = True

    normalize_url_spec = {
        'locators': {
            lambda self: self.regform
        }
    }

    def _check_access(self):
        RHRegistrationFormRegistrationBase._check_access(self)
        if self.regform.require_login and not session.user and request.method != 'GET':
            raise Forbidden(response=redirect_to_login(reason=_('You are trying to register with a form '
                                                                'that requires you to be logged in')))

    def _process_args(self):
        RHRegistrationFormRegistrationBase._process_args(self)
        InvitationMixin._process_args(self)
        if self.invitation and self.invitation.state == InvitationState.accepted and self.invitation.registration:
            return redirect(url_for('.display_regform', self.invitation.registration.locator.registrant))

    def _can_register(self):
        if self.regform.limit_reached:
            return False
        elif not self.regform.is_active and self.invitation is None:
            return False
        elif session.user and self.regform.get_registration(user=session.user):
            return False
        return True

    def _process(self):
        form = make_registration_form(self.regform)()
        if self._can_register() and form.validate_on_submit():
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
        return self.view_class.render_template('display/regform_display.html', self.event,
                                               regform=self.regform,
                                               sections=get_event_section_data(self.regform),
                                               payment_conditions=payment_event_settings.get(self.event, 'conditions'),
                                               payment_enabled=self.event.has_feature('payment'),
                                               user_data=user_data,
                                               invitation=self.invitation,
                                               registration=self.registration,
                                               management=False,
                                               login_required=self.regform.require_login and not session.user,
                                               is_restricted_access=self.is_restricted_access)


class RHRegistrationDisplayEdit(RegistrationEditMixin, RHRegistrationFormRegistrationBase):
    """Submit a registration form."""

    template_file = 'display/registration_modify.html'
    management = False
    REGISTRATION_REQUIRED = False
    ALLOW_PROTECTED_EVENT = True

    def _check_access(self):
        RHRegistrationFormRegistrationBase._check_access(self)
        if not self.registration.can_be_modified:
            raise Forbidden

    def _process_args(self):
        RHRegistrationFormRegistrationBase._process_args(self)
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


class RHRegistrationWithdraw(RHRegistrationFormRegistrationBase):
    """Withdraw a registration."""

    def _check_access(self):
        RHRegistrationFormRegistrationBase._check_access(self)
        if not self.registration.can_be_withdrawn:
            raise Forbidden

    def _process(self):
        self.registration.update_state(withdrawn=True)
        flash(_('Your registration has been withdrawn.'), 'success')
        return redirect(url_for('.display_regform', self.registration.locator.registrant))


class RHRegistrationFormDeclineInvitation(InvitationMixin, RHRegistrationFormBase):
    """Decline an invitation to register."""

    ALLOW_PROTECTED_EVENT = True

    def _process_args(self):
        RHRegistrationFormBase._process_args(self)
        InvitationMixin._process_args(self)

    def _process(self):
        if self.invitation.state == InvitationState.pending:
            self.invitation.state = InvitationState.declined
            flash(_("You declined the invitation to register."))
        return redirect(self.event.url)


class RHTicketDownload(RHRegistrationFormRegistrationBase):
    """Generate ticket for a given registration."""

    def _check_access(self):
        RHRegistrationFormRegistrationBase._check_access(self)
        if self.registration.state != RegistrationState.complete:
            raise Forbidden
        if not self.regform.tickets_enabled:
            raise Forbidden
        if (not self.regform.ticket_on_event_page and not self.regform.ticket_on_summary_page
                and not self.regform.event.can_manage(session.user, 'registration')):
            raise Forbidden
        if self.registration.is_ticket_blocked:
            raise Forbidden

    def _process(self):
        filename = secure_filename('{}-Ticket.pdf'.format(self.event.title), 'ticket.pdf')
        return send_file(filename, generate_ticket(self.registration), 'application/pdf')
