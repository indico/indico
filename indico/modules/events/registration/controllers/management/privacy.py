# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields

from indico.modules.events.registration.controllers.display import RHRegistrationFormRegistrationBase
from indico.modules.events.registration.controllers.management import RHEventManageRegFormBase
from indico.modules.events.registration.models.registrations import RegistrationVisibility
from indico.modules.events.registration.util import update_registration_consent_to_publish
from indico.modules.formify.controllers.management.privacy import RHRegistrationPrivacyMixin
from indico.web.args import use_kwargs


class RHEventRegistrationPrivacy(RHRegistrationPrivacyMixin, RHEventManageRegFormBase):
    """Change privacy settings of a registration form in an event."""


class RHAPIRegistrationChangeConsent(RHRegistrationFormRegistrationBase):
    """Internal API to change registration consent to publish."""

    @use_kwargs({'consent_to_publish': fields.Enum(RegistrationVisibility)})
    def _process_POST(self, consent_to_publish):
        update_registration_consent_to_publish(self.registration, consent_to_publish)
        return '', 204
