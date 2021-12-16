# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask.helpers import flash

from indico.core.db import db
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.controllers.management.reglists import RHRegistrationsActionBase
from indico.modules.events.registration.forms import ChangeRegistrationVisibilityForm, RegistrationPrivacyForm
from indico.modules.events.registration.models.registrations import PublishConsentType, PublishRegistrationsMode
from indico.modules.events.registration.views import WPManageRegistration
from indico.util.i18n import _
from indico.web.util import jsonify_data, jsonify_form


class RHRegistrationChangeVisibility(RHRegistrationsActionBase):
    """Change registration visibility."""

    def _process(self):
        form = ChangeRegistrationVisibilityForm(regform=self.regform,
                                                registration_id=[reg.id for reg in self.registrations],
                                                registrations=self.registrations)
        form.consent.choices = [('participants', _('Visible to participants')), ('hidden', _('Hidden'))]

        if form.validate_on_submit():
            consent_type = form.consent.data
            for reg in self.registrations:
                if consent_type == 'participants':
                    reg.consent_to_publish = PublishConsentType.participants
                elif consent_type == 'hidden':
                    reg.consent_to_publish = PublishConsentType.not_given
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
            participantVisibility, everyoneVisibility = form.visibility.data
            self.regform.publish_registrations_participants = PublishRegistrationsMode[participantVisibility]
            self.regform.publish_registrations_public = PublishRegistrationsMode[everyoneVisibility]
            db.session.flush()
            flash(_('Settings saved'), 'success')

        return WPManageRegistration.render_template('management/regform_privacy.html', self.event,
                                                    regform=self.regform, form=form)
