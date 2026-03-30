# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.admin.views import WPAdmin


class WPAffiliationsDashboard(WPAdmin):
    template_prefix = 'affiliations/'
    bundles = ('module_affiliations.dashboard.js', 'module_affiliations.dashboard.css')
