# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.registration.controllers import RHCategoryManageRegFormBase
from indico.modules.categories.views import WPCategoryManageRegistrationForm
from indico.modules.events.registration.controllers.management.privacy import RegistrationPrivacyMixin


class RHCategoryRegistrationPrivacy(RegistrationPrivacyMixin, RHCategoryManageRegFormBase):
    """Change privacy settings of a registration form in a category."""

    view_class = WPCategoryManageRegistrationForm
