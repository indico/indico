# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from uuid import uuid4

from flask import jsonify, request, session
from marshmallow import EXCLUDE, fields
from sqlalchemy.orm import joinedload
from webargs import validate
from webargs.flaskparser import abort
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.errors import UserValueError
from indico.core.notifications import make_email, send_email
from indico.core.storage.backend import StorageError
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.models.invitations import InvitationState, RegistrationInvitation
from indico.modules.events.registration.schemas import (InvitationExistingSchema, InvitationImportSchema,
                                                        InvitationNewSchema, RegistrationInvitationSchema)
from indico.modules.events.registration.util import (create_invitation, import_invitations_from_csv,
                                                     import_user_records_from_csv)
from indico.modules.events.registration.views import WPManageRegistration
from indico.modules.files.controllers import UploadFileMixin
from indico.modules.files.models.files import File
from indico.modules.logs import EventLogRealm, LogKind
from indico.util.i18n import _
from indico.util.marshmallow import (LowercaseString, make_validate_indico_placeholders, no_endpoint_links,
                                     no_relative_urls, not_empty)
from indico.util.placeholders import get_sorted_placeholders, replace_placeholders
from indico.util.spreadsheets import CSVFieldDelimiter
from indico.util.user import principal_from_identifier
from indico.web.args import parser, use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.util import jsonify_data


def _has_pending_invitations(invitations):
    return any(invitation.state == InvitationState.pending for invitation in invitations)


def _query_invitation_list(regform):
    return (RegistrationInvitation.query
            .with_parent(regform)
            .options(joinedload('registration'))
            .order_by(db.func.lower(RegistrationInvitation.first_name),
                      db.func.lower(RegistrationInvitation.last_name),
                      RegistrationInvitation.id)
            .all())


def _get_invitation_data(regform):
    invitations = _query_invitation_list(regform)
    return {
        'has_pending_invitations': _has_pending_invitations(invitations),
        'invitation_list': RegistrationInvitationSchema(many=True).dump(invitations),
    }


class RHRegistrationFormInvitations(RHManageRegFormBase):
    """Overview of all registration invitations."""

    def _process(self):
        invitations = _query_invitation_list(self.regform)
        return WPManageRegistration.render_template('management/regform_invitations.html', self.event,
                                                    regform=self.regform,
                                                    invitations_list=RegistrationInvitationSchema(many=True).dump(invitations),
                                                    has_pending_invitations=_has_pending_invitations(invitations))


class RHRegistrationFormInvite(RHManageRegFormBase):
    """Invite someone to register."""

    def _process(self):
        is_existing = request.args.get('existing') == '1'
        schema_cls = InvitationExistingSchema if is_existing else InvitationNewSchema
        data = parser.parse(schema_cls(), unknown=EXCLUDE)

        skip_moderation = data.pop('skip_moderation', False)
        skip_access_check = data.pop('skip_access_check', False)
        lock_email = data.pop('lock_email', False)

        if not self.regform.moderation_enabled:
            skip_moderation = False

        sender_address = data.pop('sender_address')
        if not (sender_address := self.event.get_verbose_email_sender(sender_address)):
            abort(422, messages={'sender_address': [_('Invalid sender address')]})

        subject = data.pop('subject')
        body = data.pop('body')

        if is_existing:
            identifiers = data.pop('users_field')
            users = self._build_users_from_identifiers(identifiers)
            field_name = 'users_field'
        else:
            users = [self._build_user_from_payload(data)]
            field_name = 'email'

        self._ensure_can_invite_emails([user['email'] for user in users], field_name)

        bcc_addresses = data.pop('bcc_addresses', [])
        copy_for_sender = data.pop('copy_for_sender', False)

        for user in users:
            create_invitation(
                self.regform,
                user,
                sender_address,
                subject,
                body,
                skip_moderation=skip_moderation,
                skip_access_check=skip_access_check,
                lock_email=lock_email,
                bcc_addresses=bcc_addresses,
                copy_for_sender=copy_for_sender,
            )

        self.regform.log(
            EventLogRealm.management, LogKind.other, 'Registration', 'Invitations sent', session.user,
            data={
                'Sender': sender_address,
                'BCC addresses': bcc_addresses,
                'CC to sender': copy_for_sender,
                'Subject': subject,
                'Body': body,
                'Skip moderation': skip_moderation,
                'Skip access check': skip_access_check,
                'Lock email': lock_email,
                '_html_fields': ['Body'],
            }
        )
        return jsonify_data(sent=len(users), skipped=0, **_get_invitation_data(self.regform))

    def _build_user_from_payload(self, data):
        return {
            'first_name': data.pop('first_name').strip(),
            'last_name': data.pop('last_name').strip(),
            'email': data.pop('email').lower(),
            'affiliation': data.pop('affiliation', ''),
        }

    def _build_users_from_identifiers(self, identifiers):
        users = []
        seen = set()
        for identifier in identifiers:
            if identifier in seen:
                continue
            seen.add(identifier)
            try:
                principal = principal_from_identifier(
                    identifier,
                    allow_external_users=True,
                    event_id=self.event.id,
                    allow_groups=False,
                    allow_event_roles=False,
                    allow_category_roles=False,
                    allow_registration_forms=False,
                    allow_emails=False,
                )
            except ValueError:
                abort(422, messages={'users_field': [_('Invalid user selection. Please refresh and try again.')]})

            email = getattr(principal, 'email', None)
            if not email:
                abort(422, messages={'users_field': [_('One of the selected users is missing an email address.')]})

            users.append({
                'first_name': principal.first_name,
                'last_name': principal.last_name,
                'email': email.lower(),
                'affiliation': principal.affiliation,
            })

        return users

    def _ensure_can_invite_emails(self, emails, field_name):
        normalized = {email.lower() for email in emails if email}
        invitation_emails = {inv.email.lower() for inv in self.regform.invitations}
        registration_emails = {
            reg.email.lower()
            for reg in self.regform.registrations
            if reg.is_active and reg.email
        }

        conflicts = invitation_emails & normalized
        if conflicts:
            abort(422, messages={
                field_name: [_('There are already invitations for the following email addresses: {emails}')
                             .format(emails=', '.join(sorted(conflicts)))]
            })

        conflicts = registration_emails & normalized
        if conflicts:
            abort(422, messages={
                field_name: [_('There are already registrations with the following email addresses: {emails}')
                             .format(emails=', '.join(sorted(conflicts)))]
            })


class RHRegistrationFormInviteMetadata(RHManageRegFormBase):
    """Provide metadata required to render the invitation dialog."""

    def _process(self):
        with self.event.force_event_locale():
            tpl = get_template_module('events/registration/emails/invitation_default.html', event=self.event)
            default_body = tpl.get_html_body()
            default_subject = tpl.get_subject()
        placeholders = get_sorted_placeholders('registration-invitation-email', invitation=None)
        return jsonify({
            'senders': list(self.event.get_allowed_sender_emails().items()),
            'default_subject': default_subject,
            'default_body': default_body,
            'moderation_enabled': self.regform.moderation_enabled,
            'placeholders': [p.serialize() for p in placeholders],
            'csv_delimiters': [{'value': delim.name, 'text': str(delim.title)} for delim in CSVFieldDelimiter],
            'default_delimiter': CSVFieldDelimiter.comma.name,
            'csv_upload_url': url_for('.api_invitations_import_upload', self.regform),
        })


class RHRegistrationFormImportInvites(RHManageRegFormBase):
    """Import invitations from a CSV file using the REST API."""

    @use_kwargs(InvitationImportSchema)
    def _process(self, sender_address, subject, body, bcc_addresses, copy_for_sender, skip_moderation,
                 skip_access_check, skip_existing, lock_email, source_file):
        if not (sender_address := self.event.get_verbose_email_sender(sender_address)):
            raise BadRequest('Invalid sender address')
        skip_moderation = skip_moderation and self.regform.moderation_enabled

        file = File.query.filter_by(uuid=str(source_file)).one_or_none()
        if (file is None or
                file.meta.get('regform_id') != self.regform.id or
                file.meta.get('delimiter') not in CSVFieldDelimiter):
            raise BadRequest('Invalid uploaded file')
        try:
            with file.open() as stream:
                invitations, skipped = import_invitations_from_csv(
                    self.regform,
                    stream,
                    sender_address,
                    subject,
                    body,
                    skip_moderation=skip_moderation,
                    skip_access_check=skip_access_check,
                    skip_existing=skip_existing,
                    lock_email=lock_email,
                    delimiter=CSVFieldDelimiter[file.meta['delimiter']].delimiter,
                    bcc_addresses=bcc_addresses,
                    copy_for_sender=copy_for_sender
                )
        except StorageError:
            db.session.delete(file)
            db.session.flush()
            abort(422, messages={'source_file': [_('The uploaded file is no longer available. Please re-upload it.')]})
        except UserValueError as exc:
            abort(422, messages={'source_file': [str(exc)]})
        file.delete(delete_from_db=True)
        return jsonify_data(skipped=skipped, sent=len(invitations), **_get_invitation_data(self.regform))


class RHRegistrationFormImportInvitesUpload(UploadFileMixin, RHManageRegFormBase):
    """Upload CSV files that will later be used for invitation import."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delimiter = None
        self._preview_sample = None

    @use_kwargs({'delimiter': fields.Enum(CSVFieldDelimiter, load_default=CSVFieldDelimiter.comma)},
                location='query')
    def _process_args(self, delimiter):
        super()._process_args()
        self.delimiter = delimiter

    def get_file_context(self):
        return 'event', self.event.id, 'regform', self.regform.id, 'invitation-import'

    def validate_file(self, file):
        if not file.filename.lower().endswith('.csv'):
            return False

        file.stream.seek(0)
        try:
            rows = import_user_records_from_csv(
                file.stream,
                columns=['first_name', 'last_name', 'affiliation', 'email'],
                delimiter=self.delimiter.delimiter
            )
        except UserValueError as exc:
            abort(422, messages={'file': [str(exc)]})
        finally:
            file.stream.seek(0)

        if not rows:
            abort(422, messages={'file': [_('The uploaded CSV file is empty')]})

        sample = rows[0]
        self._preview_sample = {'first_name': sample['first_name'], 'last_name': sample['last_name']}
        return True

    def get_file_metadata(self):
        return {
            'regform_id': self.regform.id,
            'delimiter': self.delimiter or CSVFieldDelimiter.comma.name,
            'preview_sample': self._preview_sample,
        }


class RHRegistrationFormInvitationPreview(RHManageRegFormBase):
    """Return a preview of an invitation email."""

    @use_kwargs({
        'subject': fields.String(load_default=''),
        'body': fields.String(load_default=''),
        'first_name': fields.String(load_default=None),
        'last_name': fields.String(load_default=None),
        'source_file': fields.UUID(load_default=None),
    })
    @no_autoflush
    def _process(self, subject, body, first_name, last_name, source_file):
        self.commit = False
        if source_file:
            first_name, last_name = self._get_preview_names_from_csv(source_file)
        elif not first_name:
            abort(422, messages={'first_name': ['Missing data']})
        elif not last_name:
            abort(422, messages={'last_name': ['Missing data']})

        invitation = RegistrationInvitation(
            registration_form=self.regform,
            first_name=first_name,
            last_name=last_name,
            email='',
            affiliation='',
            uuid=str(uuid4())
        )
        rendered_subject = replace_placeholders('registration-invitation-email', subject,
                                                invitation=invitation)
        rendered_body = replace_placeholders('registration-invitation-email', body, invitation=invitation)
        tpl = get_template_module('emails/custom.html', subject=rendered_subject, body=rendered_body)
        return jsonify(subject=tpl.get_subject(), body=tpl.get_body())

    def _get_preview_names_from_csv(self, source_file):
        file = File.query.filter_by(uuid=str(source_file)).first()
        if file is None or file.meta.get('regform_id') != self.regform.id:
            abort(422, messages={'source_file': ['Invalid uploaded file']})

        sample = file.meta.get('preview_sample')
        if not sample:
            abort(422, messages={
                'source_file': ['The uploaded file is missing preview data.']
            })

        return sample['first_name'], sample['last_name']


class RHPendingInvitationsBase(RHManageRegFormBase):
    """Mixin for RHs that work on pending invitations."""

    @use_kwargs({
        'invitation_ids': fields.List(fields.Int(), load_default=None),
    })
    def _process_args(self, invitation_ids):
        RHManageRegFormBase._process_args(self)
        query = (RegistrationInvitation.query.with_parent(self.regform)
                 .filter(RegistrationInvitation.state == InvitationState.pending))
        if invitation_ids is not None:
            query = query.filter(RegistrationInvitation.id.in_(invitation_ids))
        self.invitations = query.all()


class RHRegistrationFormRemindersSend(RHPendingInvitationsBase):
    """Send a reminder to pending invitees."""

    @use_kwargs({
        'sender_address': fields.String(required=True, validate=not_empty),
        'body': fields.String(required=True, validate=[
            not_empty,
            no_relative_urls,
            no_endpoint_links('event_registration.display_regform', {'invitation'}),
            make_validate_indico_placeholders('registration-invitation-reminder-email')
        ]),
        'subject': fields.String(required=True, validate=[not_empty, validate.Length(max=200)]),
        'bcc_addresses': fields.List(LowercaseString(validate=validate.Email())),
        'copy_for_sender': fields.Bool(load_default=False),
    })
    def _process(self, sender_address, body, subject, bcc_addresses, copy_for_sender):
        if not (sender_address := self.event.get_verbose_email_sender(sender_address)):
            abort(422, messages={'sender_address': ['Invalid sender address']})
        for invitation in self.invitations:
            email_body = replace_placeholders('registration-invitation-reminder-email', body, event=self.event,
                                              invitation=invitation)
            email_subject = replace_placeholders('registration-invitation-reminder-email', subject,
                                                 event=self.event, invitation=invitation)
            bcc = {session.user.email} if copy_for_sender else set()
            bcc.update(bcc_addresses)
            with self.event.force_event_locale():
                tpl = get_template_module('emails/custom.html', subject=email_subject, body=email_body)
                email = make_email(to_list=invitation.email, bcc_list=bcc, sender_address=sender_address,
                                   template=tpl, html=True)
            send_email(email, self.event, 'Registration', session.user)
            self.regform.log(
                EventLogRealm.management, LogKind.other, 'Registration', 'Invitation reminders sent', session.user,
                data={
                    'Sender': sender_address,
                    'CC to sender': copy_for_sender,
                    'Subject': subject,
                    'Body': body,
                    '_html_fields': ['Body'],
                }
            )
        return jsonify(count=len(self.invitations))


class RHRegistrationFormRemindersMetadata(RHPendingInvitationsBase):
    """Get the metadata for registration reminder emails."""

    def _process(self):
        with self.event.force_event_locale():
            tpl = get_template_module('events/registration/emails/registration_reminder_default.html', event=self.event)
            body = tpl.get_html_body()
            subject = tpl.get_subject()
        placeholders = get_sorted_placeholders('registration-invitation-reminder-email')
        recipients = sorted(invitation.email for invitation in self.invitations)
        return jsonify({
            'senders': list(self.event.get_allowed_sender_emails().items()),
            'recipients': recipients,
            'body': body,
            'subject': subject,
            'placeholders': [p.serialize() for p in placeholders],
        })


class RHRegistrationFormRemindersPreview(RHPendingInvitationsBase):
    """Preview a registration reminder email."""

    @use_kwargs({
        'body': fields.String(required=True),
        'subject': fields.String(required=True, validate=validate.Length(max=200)),
    })
    def _process(self, body, subject):
        if not self.invitations:
            raise BadRequest('No pending invitations')
        email_body = replace_placeholders('registration-invitation-reminder-email', body, event=self.event,
                                          invitation=self.invitations[0])
        email_subject = replace_placeholders('registration-invitation-reminder-email', subject, event=self.event,
                                             invitation=self.invitations[0])
        tpl = get_template_module('events/persons/emails/custom_email.html', email_subject=email_subject,
                                  email_body=email_body)
        return jsonify(subject=tpl.get_subject(), body=tpl.get_body())


class RHRegistrationFormInvitationBase(RHManageRegFormBase):
    """Base class for RH working on one invitation."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.invitation
        }
    }

    def _process_args(self):
        RHManageRegFormBase._process_args(self)
        self.invitation = RegistrationInvitation.get_or_404(request.view_args['invitation_id'])


class RHRegistrationFormDeleteInvitation(RHRegistrationFormInvitationBase):
    """Delete a registration invitation."""

    def _process(self):
        db.session.delete(self.invitation)
        return jsonify_data(**_get_invitation_data(self.regform))


class RHRegistrationFormManagerDeclineInvitation(RHRegistrationFormInvitationBase):
    """Mark a registration is declined by the invitee."""

    def _process(self):
        if self.invitation.state == InvitationState.pending:
            self.invitation.state = InvitationState.declined
            db.session.flush()
        return jsonify_data(**_get_invitation_data(self.regform))
