# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.registration.controllers import RHCategoryManageRegFormBase
from indico.modules.formify.controllers.management.privacy import RHRegistrationPrivacyMixin


class RHCategoryRegistrationPrivacy(RHRegistrationPrivacyMixin, RHCategoryManageRegFormBase):
    """Change privacy settings of a registration form in a category."""
