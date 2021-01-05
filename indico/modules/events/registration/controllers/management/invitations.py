# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, request
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.forms import InvitationFormExisting, InvitationFormNew
from indico.modules.events.registration.models.invitations import InvitationState, RegistrationInvitation
from indico.modules.events.registration.notifications import notify_invitation
from indico.modules.events.registration.views import WPManageRegistration
from indico.util.i18n import ngettext
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_template


def _query_invitation_list(regform):
    return (RegistrationInvitation.query
            .with_parent(regform)
            .options(joinedload('registration'))
            .order_by(db.func.lower(RegistrationInvitation.first_name),
                      db.func.lower(RegistrationInvitation.last_name),
                      RegistrationInvitation.id)
            .all())


def _render_invitation_list(regform):
    tpl = get_template_module('events/registration/management/_invitation_list.html')
    return tpl.render_invitation_list(_query_invitation_list(regform))


class RHRegistrationFormInvitations(RHManageRegFormBase):
    """Overview of all registration invitations."""

    def _process(self):
        invitations = _query_invitation_list(self.regform)
        return WPManageRegistration.render_template('management/regform_invitations.html', self.event,
                                                    regform=self.regform, invitations=invitations)


class RHRegistrationFormInvite(RHManageRegFormBase):
    """Invite someone to register."""

    def _create_invitation(self, user, skip_moderation, email_from, email_subject, email_body):
        invitation = RegistrationInvitation(
            skip_moderation=skip_moderation,
            email=user['email'],
            first_name=user['first_name'],
            last_name=user['last_name'],
            affiliation=user['affiliation']
        )
        self.regform.invitations.append(invitation)
        db.session.flush()
        notify_invitation(invitation, email_subject, email_body, email_from)

    def _process(self):
        tpl = get_template_module('events/registration/emails/invitation_default.html', event=self.event)
        form_cls = InvitationFormExisting if request.args.get('existing') == '1' else InvitationFormNew
        defaults = FormDefaults(email_body=tpl.get_html_body(), email_subject=tpl.get_subject())
        form = form_cls(obj=defaults, regform=self.regform)
        skip_moderation = form.skip_moderation.data if 'skip_moderation' in form else False
        if form.validate_on_submit():
            for user in form.users.data:
                self._create_invitation(user, skip_moderation, form.email_from.data,
                                        form.email_subject.data, form.email_body.data)
            num = len(form.users.data)
            flash(ngettext("The invitation has been sent.",
                           "{n} invitations have been sent.",
                           num).format(n=num), 'success')
            return jsonify_data(invitation_list=_render_invitation_list(self.regform))
        return jsonify_template('events/registration/management/regform_invite.html', regform=self.regform, form=form)


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
        return jsonify_data(invitation_list=_render_invitation_list(self.regform))


class RHRegistrationFormManagerDeclineInvitation(RHRegistrationFormInvitationBase):
    """Mark a registration is declined by the invitee."""

    def _process(self):
        if self.invitation.state == InvitationState.pending:
            self.invitation.state = InvitationState.declined
            db.session.flush()
        return jsonify_data(invitation_list=_render_invitation_list(self.regform))
