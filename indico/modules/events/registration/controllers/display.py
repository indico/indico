# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from uuid import UUID

from flask import flash, jsonify, redirect, request, session
from sqlalchemy.orm import contains_eager, joinedload, lazyload, load_only, subqueryload
from webargs import fields
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.db import db
from indico.modules.auth.util import redirect_to_login
from indico.modules.core.captcha import get_captcha_settings, invalidate_captcha
from indico.modules.events.controllers.base import RegistrationRequired, RHDisplayEventBase
from indico.modules.events.models.events import EventType
from indico.modules.events.payment import payment_event_settings
from indico.modules.events.registration import registration_settings
from indico.modules.events.registration.controllers import RegistrationEditMixin, RegistrationFormMixin
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.invitations import InvitationState, RegistrationInvitation
from indico.modules.events.registration.models.items import PersonalDataType
from indico.modules.events.registration.models.registrations import Registration, RegistrationState
from indico.modules.events.registration.notifications import notify_registration_state_update
from indico.modules.events.registration.util import (check_registration_email, create_registration, generate_ticket,
                                                     get_event_regforms_registrations, get_flat_section_submission_data,
                                                     get_initial_form_values, get_user_data, make_registration_schema)
from indico.modules.events.registration.views import (WPDisplayRegistrationFormConference,
                                                      WPDisplayRegistrationFormSimpleEvent,
                                                      WPDisplayRegistrationParticipantList)
from indico.modules.files.controllers import UploadFileMixin
from indico.modules.users.util import send_avatar, send_default_avatar
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.util.marshmallow import LowercaseString, UUIDString
from indico.web.args import parser, use_kwargs
from indico.web.flask.util import send_file, url_for
from indico.web.util import ExpectedError


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

    def _check_access(self):
        if not self.token:
            RHRegistrationFormBase._check_access(self)


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
                 .filter(Registration.is_state_publishable,
                         ~RegistrationForm.is_deleted,
                         ~RegistrationForm.participant_list_disabled)
                 .join(Registration.registration_form)
                 .options(subqueryload('data').joinedload('field_data'),
                          contains_eager('registration_form'))
                 .signal_query('merged-participant-list-publishable-registrations', event=self.event))
        is_participant = self.event.is_user_registered(session.user)
        registrations = sorted(_deduplicate_reg_data(_process_registration(reg, column_names)
                                                     for reg in query if reg.is_publishable(is_participant)),
                               key=lambda reg: tuple(x['text'].lower() for x in reg['columns']))
        return {'headers': headers,
                'rows': registrations,
                'show_checkin': any(registration['checked_in'] for registration in registrations),
                'num_participants': query.count()}

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
        query = (Registration.query.with_parent(regform)
                 .filter(Registration.is_state_publishable)
                 .options(subqueryload('data'))
                 .order_by(db.func.lower(Registration.first_name),
                           db.func.lower(Registration.last_name),
                           Registration.friendly_id)
                 .signal_query('participant-list-publishable-registrations', regform=regform))
        is_participant = self.event.is_user_registered(session.user)
        registrations = [_process_registration(reg, column_ids, active_fields) for reg in query
                         if reg.is_publishable(is_participant)]
        return {'headers': headers,
                'rows': registrations,
                'title': regform.title,
                'show_checkin': any(registration['checked_in'] for registration in registrations),
                'num_participants': query.count()}

    def _process(self):
        regforms = (RegistrationForm.query.with_parent(self.event)
                    .filter(RegistrationForm.is_participant_list_visible(self.event.is_user_registered(session.user)),
                            ~RegistrationForm.participant_list_disabled)
                    .options(subqueryload('registrations').subqueryload('data').joinedload('field_data'))
                    .signal_query('participant-list-publishable-regforms', event=self.event)
                    .all())
        if registration_settings.get(self.event, 'merge_registration_forms'):
            tables = [self._merged_participant_list_table()]
        else:
            tables = []
            regforms_dict = {regform.id: regform for regform in regforms}
            for form_id in registration_settings.get_participant_list_form_ids(self.event):
                try:
                    regform = regforms_dict.pop(form_id)
                except KeyError:
                    # The settings might reference forms that are not available
                    # anymore (publishing was disabled, etc.)
                    continue
                tables.append(self._participant_list_table(regform))
            # There might be forms that have not been sorted by the user yet
            tables.extend(map(self._participant_list_table, regforms_dict.values()))

        num_participants = sum(table['num_participants'] for table in tables)

        return self.view_class.render_template(
            'display/participant_list.html',
            self.event,
            tables=tables,
            published=bool(regforms),
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
            flash(_('Your invitation code is not valid.'), 'warning')
            return
        self.invitation = RegistrationInvitation.query.filter_by(uuid=token).with_parent(self.regform).first()
        if self.invitation is None:
            flash(_('This invitation does not exist or has been withdrawn.'), 'warning')


class RHRegistrationFormCheckEmail(RHRegistrationFormBase):
    """Check how an email will affect the registration."""

    ALLOW_PROTECTED_EVENT = True

    @use_kwargs({
        'email': LowercaseString(required=True),
        'update': UUIDString(load_default=None),
        'management': fields.Bool(load_default=False),
    }, location='query')
    def _process_args(self, email, update, management):
        RHRegistrationFormBase._process_args(self)
        self.email = email
        self.update = update
        self.management = management
        self.existing_registration = self.regform.get_registration(uuid=self.update) if self.update else None

    def _check_access(self):
        if not self.existing_registration:
            RHRegistrationFormBase._check_access(self)

    def _process(self):
        if self.update:
            return jsonify(check_registration_email(self.regform, self.email, self.existing_registration,
                                                    management=self.management))
        else:
            return jsonify(check_registration_email(self.regform, self.email, management=self.management))


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

    @property
    def _captcha_required(self):
        """Whether a CAPTCHA should be displayed when registering."""
        return session.user is None and self.regform.require_captcha

    def _can_register(self):
        if self.regform.limit_reached:
            return False
        elif self.regform.is_purged:
            return False
        elif not self.regform.is_active and self.invitation is None:
            return False
        elif session.user and self.regform.get_registration(user=session.user):
            return False
        return True

    def _process_POST(self):
        if not self._can_register():
            raise ExpectedError(_('You cannot register for this event'))

        schema = make_registration_schema(self.regform, captcha_required=self._captcha_required)()
        form_data = parser.parse(schema)
        registration = create_registration(self.regform, form_data, self.invitation)
        invalidate_captcha()
        return jsonify({'redirect': url_for('.display_regform', registration.locator.registrant)})

    def _process_GET(self):
        user_data = get_user_data(self.regform, session.user, self.invitation)
        initial_values = get_initial_form_values(self.regform) | user_data
        if self._captcha_required:
            initial_values |= {'captcha': None}
        return self.view_class.render_template('display/regform_display.html', self.event,
                                               regform=self.regform,
                                               form_data=get_flat_section_submission_data(self.regform),
                                               initial_values=initial_values,
                                               payment_conditions=payment_event_settings.get(self.event, 'conditions'),
                                               payment_enabled=self.event.has_feature('payment'),
                                               invitation=self.invitation,
                                               registration=self.registration,
                                               management=False,
                                               login_required=self.regform.require_login and not session.user,
                                               is_restricted_access=self.is_restricted_access,
                                               captcha_required=self._captcha_required,
                                               captcha_settings=get_captcha_settings())


class RHUploadRegistrationFile(UploadFileMixin, RHRegistrationFormBase):
    """
    Upload a file from a registration form.

    Regform file fields do not wait for the regform to be submitted,
    but upload the selected files immediately, saving just the genereated uuid.
    Only this uuid is then sent when the regform is submitted.
    """

    def get_file_context(self):
        return 'event', self.event.id, 'regform', self.regform.id, 'registration'


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
                flash(_('We could not find a registration for you.  If have already registered, please use the '
                        'direct access link from the email you received after registering.'), 'warning')
            else:
                flash(_('We could not find a registration for you.  If have already registered, please use the '
                        'direct access link from the email you received after registering or log in to your Indico '
                        'account.'), 'warning')
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
        notify_registration_state_update(self.registration)
        return redirect(url_for('event_registration.display_regform', self.registration.locator.registrant))


class RHRegistrationFormDeclineInvitation(InvitationMixin, RHRegistrationFormBase):
    """Decline an invitation to register."""

    ALLOW_PROTECTED_EVENT = True

    def _process_args(self):
        RHRegistrationFormBase._process_args(self)
        InvitationMixin._process_args(self)

    def _process(self):
        if self.invitation.state == InvitationState.pending:
            self.invitation.state = InvitationState.declined
            flash(_('You declined the invitation to register.'))
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
        filename = secure_filename(f'{self.event.title}-Ticket.pdf', 'ticket.pdf')
        return send_file(filename, generate_ticket(self.registration), 'application/pdf')


class RHRegistrationAvatar(RHDisplayEventBase):
    """Display a standard avatar for a registration based on the full name."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.registration
        }
    }

    def _process_args(self):
        RHDisplayEventBase._process_args(self)
        self.registration = (Registration.query
                             .filter(Registration.id == request.view_args['registration_id'],
                                     ~Registration.is_deleted,
                                     ~RegistrationForm.is_deleted)
                             .join(Registration.registration_form)
                             .options(load_only('id', 'registration_form_id', 'first_name', 'last_name'),
                                      lazyload('*'),
                                      joinedload('registration_form').load_only('id', 'event_id'),
                                      joinedload('user').load_only('id', 'first_name', 'last_name', 'title',
                                                                   'picture_source', 'picture_metadata', 'picture'))
                             .one())

    def _process(self):
        if self.registration.user:
            return send_avatar(self.registration.user)
        return send_default_avatar(self.registration.full_name)
