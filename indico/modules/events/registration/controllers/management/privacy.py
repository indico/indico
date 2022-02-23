# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask.helpers import flash
from marshmallow_enum import EnumField

from indico.core.db import db
from indico.modules.events.registration.controllers.display import RHRegistrationFormRegistrationBase
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.controllers.management.reglists import RHRegistrationsActionBase
from indico.modules.events.registration.forms import ChangeRegistrationVisibilityForm, RegistrationPrivacyForm
from indico.modules.events.registration.models.registrations import PublishConsentType, PublishRegistrationsMode
from indico.modules.events.registration.views import WPManageRegistration
from indico.util.i18n import _
from indico.web.args import use_kwargs
from indico.web.util import jsonify_data, jsonify_form


class RHRegistrationChangeVisibility(RHRegistrationsActionBase):
    """Change registration visibility."""

    def _process(self):
        form = ChangeRegistrationVisibilityForm(regform=self.regform,
                                                registration_id=[reg.id for reg in self.registrations],
                                                registrations=self.registrations)

        if form.validate_on_submit():
            consent_type = form.consent.data
            for reg in self.registrations:
                if consent_type == 'participants':
                    reg.consent_to_publish = PublishConsentType.participants
                elif consent_type == 'hidden':
                    reg.consent_to_publish = PublishConsentType.nobody
            db.session.flush()
            return jsonify_data()

        return jsonify_form(form, disabled_until_change=False)


class RHRegistrationPrivacy(RHManageRegFormBase):
    """Change privacy settings of a registration form."""

    def _process_GET(self):
        form = RegistrationPrivacyForm(event=self.event, regform=self.regform)
        form.visibility.data = [self.regform.publish_registrations_participants.name,
                                self.regform.publish_registrations_public.name]

        return WPManageRegistration.render_template('management/regform_privacy.html', self.event,
                                                    regform=self.regform, form=form)

    def _process_POST(self):
        form = RegistrationPrivacyForm(event=self.event, regform=self.regform)
        if form.validate_on_submit():
            participant_visibility, public_visibility = form.visibility.data
            self.regform.publish_registrations_participants = PublishRegistrationsMode[participant_visibility]
            self.regform.publish_registrations_public = PublishRegistrationsMode[public_visibility]
            db.session.flush()
            flash(_('Settings saved'), 'success')

        return WPManageRegistration.render_template('management/regform_privacy.html', self.event,
                                                    regform=self.regform, form=form)


class RHAPIRegistrationChangeConsent(RHRegistrationFormRegistrationBase):
    """Internal API to change registration consent to publish."""

    @use_kwargs({'consent_to_publish': EnumField(PublishConsentType)})
    def _process_POST(self, consent_to_publish):
        self.registration.consent_to_publish = consent_to_publish
        return '', 204
