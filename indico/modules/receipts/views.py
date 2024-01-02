# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.admin.views import WPAdmin
from indico.modules.categories.views import WPCategoryManagement
from indico.modules.events.management.views import WPEventManagement
from indico.web.flask.util import url_for


class WPEventReceiptTemplates(WPEventManagement):
    template_prefix = 'receipts/'
    bundles = ('monaco.js', 'monaco.css', 'module_receipts.admin.js', 'module_receipts.admin.css')


class WPCategoryReceiptTemplates(WPCategoryManagement):
    template_prefix = 'receipts/'
    bundles = ('monaco.js', 'monaco.css', 'module_receipts.admin.js', 'module_receipts.admin.css')

    def _get_parent_category_breadcrumb_url(self, category, management=False):
        if not management:
            return category.url
        # we don't want template-specific urls since those may be tied
        # to the previous category
        return url_for('receipts.template_list', category)


class WPReceiptsAdmin(WPAdmin):
    template_prefix = 'receipts/'
