# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.controllers.base import RHManageCategoryBase
from indico.modules.events.registration.controllers import RegistrationFormMixin


class RHCategoryManageRegformsBase(RHManageCategoryBase):
    """Base class for all category registration form management RHs."""


class RHCategoryManageRegFormBase(RegistrationFormMixin, RHCategoryManageRegformsBase):
    """Base class for a specific registration form in a category."""

    def _process_args(self):
        RHCategoryManageRegformsBase._process_args(self)
        RegistrationFormMixin._process_args(self)
