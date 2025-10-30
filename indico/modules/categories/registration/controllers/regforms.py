# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.registration.controllers import RHCategoryManageRegFormBase, RHCategoryManageRegformsBase
from indico.modules.categories.views import WPCategoryManageRegistrationForm
from indico.modules.registration_form.controllers.management.regforms import (ManageRegistrationFormsAreaMixin,
                                                                              ManageRegistrationFormsMixin,
                                                                              RegistrationFormCreateMixin,
                                                                              RegistrationFormDeleteMixin,
                                                                              RegistrationFormEditMixin,
                                                                              RegistrationFormModifyMixin)


class RHCategoryManageRegistrationForms(ManageRegistrationFormsMixin, RHCategoryManageRegformsBase):
    """List all registrations forms for a category."""


class RHCategoryRegistrationFormCreate(RegistrationFormCreateMixin, RHCategoryManageRegformsBase):
    """Create a new registration form for a category."""


class RHCategoryRegistrationFormManage(ManageRegistrationFormsAreaMixin, RHCategoryManageRegFormBase):
    """Specific category registration form management."""

    def _process(self):
        return WPCategoryManageRegistrationForm.render_template('management/regform.html', self.category,
                                                            regform=self.regform)


class RHCategoryRegistrationFormEdit(RegistrationFormEditMixin, RHCategoryManageRegFormBase):
    """Edit a registration form in a categoory."""


class RHCategoryRegistrationFormDelete(RegistrationFormDeleteMixin, RHCategoryManageRegFormBase):
    """Delete a registration form in a category."""


class RHCategoryRegistrationFormModify(RegistrationFormModifyMixin, RHCategoryManageRegFormBase):
    """Modify the form of a registration form for a category."""
