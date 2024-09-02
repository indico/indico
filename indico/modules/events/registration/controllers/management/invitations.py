# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, jsonify, request, session
from marshmallow import fields
from sqlalchemy.orm import joinedload
from webargs import validate
from webargs.flaskparser import abort
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.core.notifications import make_email, send_email
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.forms import ImportInvitationsForm, InvitationFormExisting, InvitationFormNew
from indico.modules.events.registration.models.invitations import InvitationState, RegistrationInvitation
from indico.modules.events.registration.util import create_invitation, import_invitations_from_csv
from indico.modules.events.registration.views import WPManageRegistration
from indico.util.i18n import ngettext
from indico.util.marshmallow import LowercaseString, no_relative_urls, not_empty
from indico.util.placeholders import get_sorted_placeholders, replace_placeholders
from indico.web.args import use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_template


def _has_pending_invitations(invitations):
    return any(invitation.state == InvitationState.pending for invitation in invitations)


def _query_pending_invitations(regform):
    return (RegistrationInvitation.query.with_parent(regform)
            .filter(RegistrationInvitation.state == InvitationState.pending)
            .all())


def _query_invitation_list(regform):
    return (RegistrationInvitation.query
            .with_parent(regform)
            .options(joinedload('registration'))
            .order_by(db.func.lower(RegistrationInvitation.first_name),
                      db.func.lower(RegistrationInvitation.last_name),
                      RegistrationInvitation.id)
            .all())


def _render_invitation_list(invitations):
    tpl = get_template_module('events/registration/management/_invitation_list.html')
    return tpl.render_invitation_list(invitations)


def _get_invitation_data(regform):
    invitations = _query_invitation_list(regform)
    return {
        'invitation_list': _render_invitation_list(invitations),
        'has_pending_invitations': _has_pending_invitations(invitations)
    }


class RHRegistrationFormInvitations(RHManageRegFormBase):
    """Overview of all registration invitations."""

    def _process(self):
        invitations = _query_invitation_list(self.regform)
        return WPManageRegistration.render_template('management/regform_invitations.html', self.event,
                                                    regform=self.regform, invitations=invitations,
                                                    has_pending_invitations=_has_pending_invitations(invitations))


class RHRegistrationFormInvite(RHManageRegFormBase):
    """Invite someone to register."""

    def _process(self):
        with self.event.force_event_locale():
            tpl = get_template_module('events/registration/emails/invitation_default.html', event=self.event)
            defaults = FormDefaults(email_body=tpl.get_html_body(), email_subject=tpl.get_subject())
        form_cls = InvitationFormExisting if request.args.get('existing') == '1' else InvitationFormNew
        form = form_cls(obj=defaults, regform=self.regform)
        skip_moderation = form.skip_moderation.data if 'skip_moderation' in form else False
        skip_access_check = form.skip_access_check.data
        if form.validate_on_submit():
            for user in form.users.data:
                create_invitation(self.regform, user, form.email_from.data, form.email_subject.data,
                                  form.email_body.data,
                                  skip_moderation=skip_moderation, skip_access_check=skip_access_check)
            num = len(form.users.data)
            flash(ngettext('The invitation has been sent.',
                           '{n} invitations have been sent.',
                           num).format(n=num), 'success')
            return jsonify_data(**_get_invitation_data(self.regform))
        return jsonify_template('events/registration/management/regform_invite.html', regform=self.regform, form=form)


class RHRegistrationFormRemindersSend(RHManageRegFormBase):
    """Send a reminder to pending invitees."""

    @use_kwargs({
        'from_address': fields.String(required=True, validate=not_empty),
        'body': fields.String(required=True, validate=[not_empty, no_relative_urls]),
        'subject': fields.String(required=True, validate=not_empty),
        'bcc_addresses': fields.List(LowercaseString(validate=validate.Email())),
        'copy_for_sender': fields.Bool(load_default=False),
    })
    def _process(self, from_address, body, subject, bcc_addresses, copy_for_sender):
        if from_address not in self.event.get_allowed_sender_emails():
            abort(422, messages={'from_address': ['Invalid sender address']})
        invitations = _query_pending_invitations(self.regform)
        for invitation in invitations:
            email_body = replace_placeholders('registration-invitation-reminder-email', body, event=self.event,
                                              invitation=invitation)
            email_subject = replace_placeholders('registration-invitation-reminder-email', subject,
                                                 event=self.event, invitation=invitation)
            bcc = {session.user.email} if copy_for_sender else set()
            bcc.update(bcc_addresses)
            with self.event.force_event_locale():
                tpl = get_template_module('emails/custom.html', subject=email_subject, body=email_body)
                email = make_email(to_list=invitation.email, bcc_list=bcc, from_address=from_address,
                                   template=tpl, html=True)
            send_email(email, self.event, 'Registration')
        return jsonify(count=len(invitations))


class RHRegistrationFormRemindersMetadata(RHManageRegFormBase):
    """Get the metadata for registration reminder emails."""

    def _process(self):
        with self.event.force_event_locale():
            tpl = get_template_module('events/registration/emails/registration_reminder_default.html', event=self.event)
            body = tpl.get_html_body()
            subject = tpl.get_subject()
        placeholders = get_sorted_placeholders('registration-invitation-reminder-email')
        invitations = _query_pending_invitations(self.regform)
        recipients = sorted(invitation.email for invitation in invitations)
        return jsonify({
            'senders': list(self.event.get_allowed_sender_emails().items()),
            'recipients': recipients,
            'body': body,
            'subject': subject,
            'placeholders': [p.serialize() for p in placeholders],
        })


class RHRegistrationFormRemindersPreview(RHManageRegFormBase):
    """Preview a registration reminder email."""

    @use_kwargs({
        'body': fields.String(required=True),
        'subject': fields.String(required=True),
    })
    def _process(self, body, subject):
        invitations = _query_pending_invitations(self.regform)
        if not invitations:
            raise BadRequest('No pending invitations')
        email_body = replace_placeholders('registration-invitation-reminder-email', body, event=self.event,
                                          invitation=invitations[0])
        email_subject = replace_placeholders('registration-invitation-reminder-email', subject, event=self.event,
                                             invitation=invitations[0])
        tpl = get_template_module('events/persons/emails/custom_email.html', email_subject=email_subject,
                                  email_body=email_body)
        return jsonify(subject=tpl.get_subject(), body=tpl.get_body())


class RHRegistrationFormInviteImport(RHManageRegFormBase):
    """Import invitations from a CSV file."""

    def _format_flash_message(self, sent, skipped):
        sent_msg = ngettext('One invitation has been sent.', '{n} invitations have been sent.', sent).format(n=sent)
        if not skipped:
            return sent_msg
        skipped_msg = ngettext('One invitation was skipped.',
                               '{n} invitations were skipped.', skipped).format(n=skipped)
        return f'{sent_msg} {skipped_msg}'

    def _process(self):
        with self.event.force_event_locale():
            tpl = get_template_module('events/registration/emails/invitation_default.html', event=self.event)
            defaults = FormDefaults(email_body=tpl.get_html_body(), email_subject=tpl.get_subject())
        form = ImportInvitationsForm(obj=defaults, regform=self.regform)
        if form.validate_on_submit():
            skip_moderation = form.skip_moderation.data if 'skip_moderation' in form else False
            skip_access_check = form.skip_access_check.data
            skip_existing = form.skip_existing.data
            delimiter = form.delimiter.data.delimiter
            invitations, skipped = import_invitations_from_csv(self.regform, form.source_file.data,
                                                               form.email_from.data, form.email_subject.data,
                                                               form.email_body.data,
                                                               skip_moderation=skip_moderation,
                                                               skip_access_check=skip_access_check,
                                                               skip_existing=skip_existing,
                                                               delimiter=delimiter)
            sent = len(invitations)
            flash(self._format_flash_message(sent, skipped), 'success' if sent > 0 else 'warning')
            return jsonify_data(**_get_invitation_data(self.regform))
        return jsonify_template('events/registration/management/import_invitations.html', form=form,
                                regform=self.regform)


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
