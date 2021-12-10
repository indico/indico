# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.registration.controllers.management.reglists import RHRegistrationsActionBase
from indico.modules.events.registration.forms import ChangeRegistrationVisibilityForm
from indico.modules.events.registration.models.registrations import PublishConsentType
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
                elif consent_type == 'hide':
                    reg.consent_to_publish = PublishConsentType.not_given

            return jsonify_data()

        return jsonify_form(form, disabled_until_change=False)
