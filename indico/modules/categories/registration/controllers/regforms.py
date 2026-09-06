# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.registration.controllers import RHCategoryManageRegFormBase, RHCategoryManageRegformsBase
from indico.modules.categories.views import WPCategoryManageRegistrationForm
from indico.modules.events.registration.controllers.management.regforms import (ManageRegistrationFormMixin,
                                                                                ManageRegistrationFormsMixin,
                                                                                RegistrationFormCloneMixin,
                                                                                RegistrationFormCreateMixin,
                                                                                RegistrationFormDeleteMixin,
                                                                                RegistrationFormEditMixin,
                                                                                RegistrationFormModifyMixin)


class RHCategoryManageRegistrationForms(ManageRegistrationFormsMixin, RHCategoryManageRegformsBase):
    """List all registration forms for a category."""

    view_class = WPCategoryManageRegistrationForm


class RHCategoryRegistrationFormCreate(RegistrationFormCreateMixin, RHCategoryManageRegformsBase):
    """Create a new registration form for a category."""

    view_class = WPCategoryManageRegistrationForm


class RHCategoryRegistrationFormManage(ManageRegistrationFormMixin, RHCategoryManageRegFormBase):
    """Specific category registration form management."""

    view_class = WPCategoryManageRegistrationForm


class RHCategoryRegistrationFormEdit(RegistrationFormEditMixin, RHCategoryManageRegFormBase):
    """Edit a registration form in a category."""

    view_class = WPCategoryManageRegistrationForm


class RHCategoryRegistrationFormDelete(RegistrationFormDeleteMixin, RHCategoryManageRegFormBase):
    """Delete a registration form in a category."""


class RHCategoryRegistrationFormClone(RegistrationFormCloneMixin, RHCategoryManageRegFormBase):
    """Clone a registration form in a category."""


class RHCategoryRegistrationFormModify(RegistrationFormModifyMixin, RHCategoryManageRegFormBase):
    """Modify the form of a registration form for a category."""

    view_class = WPCategoryManageRegistrationForm
