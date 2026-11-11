# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os

from flask import jsonify, request, session
from marshmallow import fields
from PIL import Image
from sqlalchemy.orm import joinedload
from webargs import validate
from webargs.flaskparser import abort
from werkzeug.exceptions import BadRequest

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.errors import UserValueError
from indico.core.notifications import make_email, send_email
from indico.modules.events.registration.constants import EMAIL_IMAGE_META_KEY
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.fields.affiliation import AffiliationMode
from indico.modules.events.registration.models.invitations import (InvitationState, MockRegistrationInvitation,
                                                                   RegistrationInvitation)
from indico.modules.events.registration.models.items import PersonalDataType
from indico.modules.events.registration.schemas import (InvitationImportSchema, InvitationUserSchema,
                                                        NewInvitationSchema, RegistrationInvitationSchema)
from indico.modules.events.registration.util import (create_invitation, embed_email_images,
                                                     import_invitations_from_user_records, import_user_records_from_csv)
from indico.modules.events.registration.views import WPManageRegistration
from indico.modules.files.models.files import File
from indico.modules.files.util import validate_upload_file_size
from indico.modules.logs import EventLogRealm, LogKind
from indico.util.fs import secure_client_filename
from indico.util.i18n import _
from indico.util.marshmallow import (LowercaseString, Principal, make_validate_indico_placeholders, no_endpoint_links,
                                     no_relative_urls, not_empty)
from indico.util.placeholders import get_sorted_placeholders, replace_placeholders
from indico.web.args import use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.util import jsonify_data


def _get_image_type(stream):
    try:
        with Image.open(stream) as image:
            image_type = image.format.lower()
    except (OSError, ValueError, Image.DecompressionBombError):
        image_type = None
    # XXX: mpo is basically JPEG and JPEGs from some cameras are (wrongfully) detected as mpo
    image_type = 'jpeg' if image_type == 'mpo' else image_type
    if image_type not in {'jpeg', 'png', 'gif'}:
        abort(422, messages={'upload': [_('Only JPG, PNG and GIF images are allowed')]})
    stream.seek(0)
    return image_type


def _exceeds_email_attachment_limit(upload):
    if config.MAX_EMAIL_ATTACHMENT_SIZE is None:
        return False
    upload.seek(0, os.SEEK_END)
    size = upload.tell()
    upload.seek(0)
    return size > config.MAX_EMAIL_ATTACHMENT_SIZE * 1024 * 1024


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

    @use_kwargs(NewInvitationSchema)
    def _process(self, sender_address, subject, body, bcc_addresses, copy_for_sender, skip_moderation,
                 skip_access_check, lock_email, user, users):
        if not (sender_address := self.event.get_verbose_email_sender(sender_address)):
            raise BadRequest('Invalid sender address')
        if not self.regform.moderation_enabled:
            skip_moderation = False

        if users:
            users = InvitationUserSchema(many=True).dump(users)
            field_name = 'users'
        else:
            users = [user]
            field_name = 'email'

        self._ensure_can_invite_emails([user_['email'] for user_ in users], field_name)

        for user_ in users:
            create_invitation(
                self.regform,
                user_,
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
        affiliation_field = self.regform.get_personal_data_field(PersonalDataType.affiliation)
        allow_affiliations = not (
            affiliation_field and
            affiliation_field.input_type == 'affiliation' and
            affiliation_field.data.get('affiliation_mode') == AffiliationMode.predefined
        )
        return jsonify({
            'senders': list(self.event.get_allowed_sender_emails(plugin_ctx={'regform': self.regform,
                                                                             'email_context': 'invitation'}).items()),
            'default_subject': default_subject,
            'default_body': default_body,
            'moderation_enabled': self.regform.moderation_enabled,
            'allow_affiliations': allow_affiliations,
            'placeholders': [p.serialize() for p in placeholders],
            'csv_upload_url': url_for('.api_invitations_import_upload', self.regform),
        })


class RHRegistrationFormImportInvites(RHManageRegFormBase):
    """Import invitations from a CSV file using the REST API."""

    @use_kwargs(InvitationImportSchema)
    def _process(self, sender_address, subject, body, bcc_addresses, copy_for_sender, skip_moderation,
                 skip_access_check, skip_existing, lock_email, imported):
        if not (sender_address := self.event.get_verbose_email_sender(sender_address)):
            raise BadRequest('Invalid sender address')

        try:
            invitations, skipped = import_invitations_from_user_records(
                self.regform,
                imported,
                sender_address,
                subject,
                body,
                skip_moderation=skip_moderation and self.regform.moderation_enabled,
                skip_access_check=skip_access_check,
                skip_existing=skip_existing,
                lock_email=lock_email,
                bcc_addresses=bcc_addresses,
                copy_for_sender=copy_for_sender
            )
        except UserValueError as exc:
            abort(422, messages={'imported': [str(exc)]})
        return jsonify(skipped=skipped, sent=len(invitations), **_get_invitation_data(self.regform))


class RHRegistrationFormImportInvitesUpload(RHManageRegFormBase):
    """Process a CSV file into invitation user records."""

    @use_kwargs({'file': fields.Raw(required=True)}, location='files')
    def _process(self, file):
        if not file.filename.lower().endswith('.csv'):
            raise BadRequest('Not a CSV file')
        try:
            rows = import_user_records_from_csv(
                file.stream,
                columns=['first_name', 'last_name', 'affiliation', 'email'],
                check_email_dns=False
            )
        except UserValueError as exc:
            abort(422, messages={'file': [str(exc)]})
        if not rows:
            abort(422, messages={'file': [_('The uploaded CSV file is empty')]})
        return InvitationUserSchema(many=True).jsonify(rows)


class RHRegistrationFormInvitationImageUpload(RHManageRegFormBase):
    """Upload an image to embed in the emails sent to invitees."""

    @use_kwargs({'upload': fields.Raw(required=True)}, location='files')
    def _process(self, upload):
        if not validate_upload_file_size(upload):
            abort(422, messages={'upload': [_('The uploaded file is too large')]})
        if _exceeds_email_attachment_limit(upload):
            abort(422, messages={'upload': [_('The image is too large to be sent by email (max. {} MB)')
                                            .format(config.MAX_EMAIL_ATTACHMENT_SIZE)]})
        image_type = _get_image_type(upload.stream)
        context = ('event', self.event.id, 'regform', self.regform.id, 'email-images')
        filename = secure_client_filename(upload.filename)
        image = File.create_from_stream(upload.stream, filename, f'image/{image_type}', context)
        # the uuid is still a string until the file is reloaded, which breaks the signed url
        db.session.refresh(image)
        image.meta = {EMAIL_IMAGE_META_KEY: self.regform.id}
        return jsonify(url=image.signed_download_url)


class RHRegistrationFormInvitationPreview(RHManageRegFormBase):
    """Return a preview of an invitation email."""

    @use_kwargs({
        'subject': fields.String(load_default=''),
        'body': fields.String(load_default=''),
        'first_name': fields.String(load_default=None),
        'last_name': fields.String(load_default=None),
        'user': Principal(load_default=None),
    })
    @no_autoflush
    def _process(self, subject, body, first_name, last_name, user):
        if user:
            first_name = user.first_name
            last_name = user.last_name
        elif not first_name:
            abort(422, messages={'first_name': ['Missing data']})
        elif not last_name:
            abort(422, messages={'last_name': ['Missing data']})

        invitation = MockRegistrationInvitation(self.regform, first_name, last_name)
        rendered_subject = replace_placeholders('registration-invitation-email', subject,
                                                invitation=invitation)
        rendered_body = replace_placeholders('registration-invitation-email', body, invitation=invitation)
        tpl = get_template_module('emails/custom.html', subject=rendered_subject, body=rendered_body)
        return jsonify(subject=tpl.get_subject(), body=tpl.get_body())


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
                rendered_body = tpl.get_body()
                rendered_subject = tpl.get_subject()
            try:
                html_body, images = embed_email_images(self.regform, rendered_body)
                email = make_email(to_list=invitation.email, bcc_list=bcc, sender_address=sender_address,
                                   subject=rendered_subject, body=html_body, attachments=images, html=True)
            except ValueError as exc:
                abort(422, messages=[str(exc)])
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
