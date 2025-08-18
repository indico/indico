# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.views import WPCategoryManagement
from indico.modules.events.management.views import WPEventManagement
from indico.web.flask.util import url_for


class WPEventManagementEmailTemplate(WPEventManagement):
    template_prefix = 'email_templates/'


class WPCategoryManagementEmailTemplate(WPCategoryManagement):
    template_prefix = 'email_templates/'

    def _get_parent_category_breadcrumb_url(self, category, management=False):
        return url_for('email_templates.email_template_list', category) if management else category.url
