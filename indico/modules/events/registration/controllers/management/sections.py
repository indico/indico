# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.registration.controllers.management import RHEventManageRegFormBase
from indico.modules.formify.controllers.management.sections import (ManageRegFormSectionBaseMixin,
                                                                    RegistrationFormAddSectionMixin,
                                                                    RegistrationFormModifySectionMixin,
                                                                    RegistrationFormMoveSection,
                                                                    RegistrationFormToggleSection)


class RHEventManageRegFormSectionBase(ManageRegFormSectionBaseMixin, RHEventManageRegFormBase):
    """Base class for a specific registration form section in an event."""

    def _process_args(self):
        RHEventManageRegFormBase._process_args(self)
        ManageRegFormSectionBaseMixin._process_args(self)


class RHEventRegistrationFormAddSection(RegistrationFormAddSectionMixin, RHEventManageRegFormBase):
    """Add a section to the registration form inside an event."""


class RHEventRegistrationFormModifySection(RegistrationFormModifySectionMixin, RHEventManageRegFormSectionBase):
    """Delete/modify a section inside an event."""


class RHEventRegistrationFormToggleSection(RegistrationFormToggleSection, RHEventManageRegFormSectionBase):
    """Enable/disable a section inside an event."""


class RHEventRegistrationFormMoveSection(RegistrationFormMoveSection, RHEventManageRegFormSectionBase):
    """Move a section within the registration form inside an event."""
