# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import redirect, session
from flask.helpers import flash
from marshmallow import fields

from indico.core.db import db
from indico.modules.events.registration.controllers.display import RHRegistrationFormRegistrationBase
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.forms import RegistrationPrivacyForm
from indico.modules.events.registration.models.registrations import RegistrationVisibility
from indico.modules.events.registration.util import update_registration_consent_to_publish
from indico.modules.events.registration.views import WPManageRegistration
from indico.modules.logs.models.entries import LogKind
from indico.modules.logs.util import make_diff_log
from indico.util.i18n import _
from indico.web.args import use_kwargs
from indico.web.flask.util import url_for


class RegistrationPrivacyMixin:
    """Change privacy settings of a registration form."""

    view_class = None
    _log_fields = {
        'publish_registrations_participants': {'title': 'Visibility to participants'},
        'publish_registrations_public': {'title': 'Visibility to everyone'},
        'publish_registrations_duration': {'title': 'Visibility duration', 'default': 'Indefinite'},
        'retention_period': {'title': 'Retention period', 'default': 'Indefinite'},
        'require_privacy_policy_agreement': {'title': 'Privacy policy'},
    }

    def _process(self):
        form = RegistrationPrivacyForm(
            regform=self.regform,
            retention_period=self.regform.retention_period,
            require_privacy_policy_agreement=self.regform.require_privacy_policy_agreement,
            visibility=[
                self.regform.publish_registrations_participants.name,
                self.regform.publish_registrations_public.name,
                (self.regform.publish_registrations_duration.days // 7
                 if self.regform.publish_registrations_duration is not None else None)
            ]
        )
        if form.validate_on_submit():
            changes = self.regform.populate_from_dict(form.data)
            db.session.flush()
            self.regform.log(self.log_realm, LogKind.change, 'Privacy',
                             f'Privacy settings for "{self.regform.title}" modified', session.user,
                             data={'Changes': make_diff_log(changes, self._log_fields)})
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.manage_registration_privacy_settings', self.regform))

        return self.view_class.render_template('management/regform_privacy.html', self.target,
                                               regform=self.regform, form=form)


class RHRegistrationPrivacy(RegistrationPrivacyMixin, RHManageRegFormBase):
    """Change privacy settings of a registration form in an event."""

    view_class = WPManageRegistration


class RHAPIRegistrationChangeConsent(RHRegistrationFormRegistrationBase):
    """Internal API to change registration consent to publish."""

    @use_kwargs({'consent_to_publish': fields.Enum(RegistrationVisibility)})
    def _process_POST(self, consent_to_publish):
        update_registration_consent_to_publish(self.registration, consent_to_publish)
        return '', 204
