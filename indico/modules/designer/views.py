# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.views import WPCategoryManagement
from indico.modules.events.management.views import WPEventManagement
from indico.web.flask.util import url_for


class WPEventManagementDesigner(WPEventManagement):
    template_prefix = 'designer/'
    bundles = ('module_designer.js',)


class WPCategoryManagementDesigner(WPCategoryManagement):
    template_prefix = 'designer/'
    bundles = ('module_designer.js',)

    def _get_parent_category_breadcrumb_url(self, category, management=False):
        if not management:
            return category.url
        # we don't want template-specific urls since those may be tied
        # to the previous category
        return url_for('designer.template_list', category)
