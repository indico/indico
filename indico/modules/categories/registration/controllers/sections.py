# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.registration.controllers import RHCategoryManageRegFormBase
from indico.modules.formify.controllers.management.sections import (ManageRegFormSectionBaseMixin,
                                                                    RegistrationFormAddSectionMixin,
                                                                    RegistrationFormModifySectionMixin,
                                                                    RegistrationFormMoveSection,
                                                                    RegistrationFormToggleSection)


class RHCategoryManageRegFormSectionBase(ManageRegFormSectionBaseMixin, RHCategoryManageRegFormBase):
    """Base class for a specific registration form section in a category."""

    def _process_args(self):
        RHCategoryManageRegFormBase._process_args(self)
        ManageRegFormSectionBaseMixin._process_args(self)


class RHCategoryRegistrationFormAddSection(RegistrationFormAddSectionMixin, RHCategoryManageRegFormBase):
    """Add a section to the registration form inside a category."""


class RHCategoryRegistrationFormModifySection(RegistrationFormModifySectionMixin,
                                                   RHCategoryManageRegFormSectionBase):
    """Delete/modify a section inside a category."""


class RHCategoryRegistrationFormToggleSection(RegistrationFormToggleSection, RHCategoryManageRegFormSectionBase):
    """Enable/disable a section inside a category."""


class RHCategoryRegistrationFormMoveSection(RegistrationFormMoveSection, RHCategoryManageRegFormSectionBase):
    """Move a section within the registration form insdie a category."""
