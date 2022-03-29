# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

from flask import redirect
from flask.helpers import flash
from marshmallow_enum import EnumField

from indico.core.db import db
from indico.modules.events.registration.controllers.display import RHRegistrationFormRegistrationBase
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.forms import RegistrationPrivacyForm
from indico.modules.events.registration.models.registrations import PublishRegistrationsMode, RegistrationVisibility
from indico.modules.events.registration.views import WPManageRegistration
from indico.util.i18n import _
from indico.web.args import use_kwargs
from indico.web.flask.util import url_for


class RHRegistrationPrivacy(RHManageRegFormBase):
    """Change privacy settings of a registration form."""

    def _process(self):
        form = RegistrationPrivacyForm(event=self.event, regform=self.regform, visibility=[
            self.regform.publish_registrations_participants.name,
            self.regform.publish_registrations_public.name,
            (self.regform.publish_registrations_duration.days // 30
             if self.regform.publish_registrations_duration is not None else None)
        ])
        if form.validate_on_submit():
            participant_visibility, public_visibility, visibility_duration = form.visibility.data
            self.regform.publish_registrations_participants = PublishRegistrationsMode[participant_visibility]
            self.regform.publish_registrations_public = PublishRegistrationsMode[public_visibility]
            self.regform.publish_registrations_duration = (timedelta(days=visibility_duration*30)
                                                           if visibility_duration is not None else None)
            db.session.flush()
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.manage_registration_privacy_settings', self.regform))

        return WPManageRegistration.render_template('management/regform_privacy.html', self.event,
                                                    regform=self.regform, form=form)


class RHAPIRegistrationChangeConsent(RHRegistrationFormRegistrationBase):
    """Internal API to change registration consent to publish."""

    @use_kwargs({'consent_to_publish': EnumField(RegistrationVisibility)})
    def _process_POST(self, consent_to_publish):
        self.registration.consent_to_publish = consent_to_publish
        return '', 204
