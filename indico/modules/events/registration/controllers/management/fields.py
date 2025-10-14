# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.registration.controllers.management import RHEventManageRegFormBase
from indico.modules.events.registration.controllers.management.sections import RHEventManageRegFormSectionBase
from indico.modules.formify.controllers.management.fields import (ManageRegFormFieldBaseMixin,
                                                                  RegistrationFormAddFieldMixin,
                                                                  RegistrationFormAddTextMixin,
                                                                  RegistrationFormModifyFieldMixin,
                                                                  RegistrationFormModifyTextMixin,
                                                                  RegistrationFormMoveFieldMixin,
                                                                  RegistrationFormMoveTextMixin,
                                                                  RegistrationFormToggleFieldStateMixin,
                                                                  RegistrationFormToggleTextStateMixin)


class RHEventManageRegformFieldBase(ManageRegFormFieldBaseMixin, RHEventManageRegFormBase):
    """Base class for a specific field within a registration form in an event."""

    def _process_args(self):
        ManageRegFormFieldBaseMixin._process_args(self)
        RHEventManageRegFormBase._process_args(self)


class RHEventRegistrationFormToggleFieldState(RegistrationFormToggleFieldStateMixin, RHEventManageRegformFieldBase):
    """Enable/Disable a field inside an event."""


class RHEventRegistrationFormModifyField(RegistrationFormModifyFieldMixin, RHEventManageRegformFieldBase):
    """Remove/Modify a field inside an event."""


class RHEventRegistrationFormMoveField(RegistrationFormMoveFieldMixin, RHEventManageRegformFieldBase):
    """Change position of a field within the section in an event."""


class RHEventRegistrationFormAddField(RegistrationFormAddFieldMixin, RHEventManageRegFormSectionBase):
    """Add a field to the section inside an event."""


class RHEventRegistrationFormToggleTextState(RegistrationFormToggleTextStateMixin, RHEventManageRegformFieldBase):
    """Enable/Disable a static text field inside an event."""


class RHEventRegistrationFormModifyText(RegistrationFormModifyTextMixin, RHEventManageRegformFieldBase):
    """Remove/Modify a static text field inside an event."""


class RHEventRegistrationFormMoveText(RegistrationFormMoveTextMixin, RHEventManageRegformFieldBase):
    """Change position of a static text field within the section of an event."""


class RHEventRegistrationFormAddText(RegistrationFormAddTextMixin, RHEventManageRegFormSectionBase):
    """Add a static text field to a section inside an event."""
