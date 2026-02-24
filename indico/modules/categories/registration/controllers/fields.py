# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.registration.controllers import RHCategoryManageRegFormBase
from indico.modules.categories.registration.controllers.sections import RHCategoryManageRegFormSectionBase
from indico.modules.formify.controllers.management.fields import (ManageRegFormFieldBaseMixin,
                                                                  RegistrationFormAddFieldMixin,
                                                                  RegistrationFormAddTextMixin,
                                                                  RegistrationFormModifyFieldMixin,
                                                                  RegistrationFormModifyTextMixin,
                                                                  RegistrationFormMoveFieldMixin,
                                                                  RegistrationFormMoveTextMixin,
                                                                  RegistrationFormToggleFieldStateMixin,
                                                                  RegistrationFormToggleTextStateMixin)


class RHCategoryManageRegformFieldBase(ManageRegFormFieldBaseMixin, RHCategoryManageRegFormBase):
    """Base class for a specific field within a registration form in a category."""

    def _process_args(self):
        RHCategoryManageRegFormBase._process_args(self)
        ManageRegFormFieldBaseMixin._process_args(self)


class RHCategoryRegistrationFormToggleFieldState(RegistrationFormToggleFieldStateMixin,
                                                  RHCategoryManageRegformFieldBase):
    """Enable/Disable a field inside a category."""


class RHCategoryRegistrationFormModifyField(RegistrationFormModifyFieldMixin, RHCategoryManageRegformFieldBase):
    """Remove/Modify a field inside a category."""


class RHCategoryRegistrationFormMoveField(RegistrationFormMoveFieldMixin, RHCategoryManageRegformFieldBase):
    """Change position of a field within the section in a category."""


class RHCategoryRegistrationFormAddField(RegistrationFormAddFieldMixin, RHCategoryManageRegFormSectionBase):
    """Add a field to the section inside a category."""


class RHCategoryRegistrationFormToggleTextState(RegistrationFormToggleTextStateMixin, RHCategoryManageRegformFieldBase):
    """Enable/Disable a static text field inside a category."""


class RHCategoryRegistrationFormModifyText(RegistrationFormModifyTextMixin, RHCategoryManageRegformFieldBase):
    """Remove/Modify a static text field inside a category."""


class RHCategoryRegistrationFormMoveText(RegistrationFormMoveTextMixin, RHCategoryManageRegformFieldBase):
    """Change position of a static text field within the section of a category."""


class RHCategoryRegistrationFormAddText(RegistrationFormAddTextMixin, RHCategoryManageRegFormSectionBase):
    """Add a static text field to a section inside a category."""
