# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.controllers.base import RHManageCategoryBase
from indico.modules.categories.forms import CategoryPrivacyForm
from indico.modules.categories.operations import get_category_privacy, update_category_privacy
from indico.modules.categories.views import WPCategoryManagement
from indico.modules.events.management.controllers.privacy import RHPrivacyMixin
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHCategoryPrivacy(RHPrivacyMixin, RHManageCategoryBase):
    """Show category privacy dashboard."""

    def _get_privacy_data(self):
        return get_category_privacy(self.category)

    def _update_privacy(self, data):
        update_category_privacy(self.category, data)

    def _get_form(self, **kwargs):
        return CategoryPrivacyForm(obj=FormDefaults(**kwargs), category=self.category)

    def _redirect_url(self):
        return url_for('.manage_privacy_dashboard', self.category)

    def _render_template(self, **kwargs):
        return WPCategoryManagement.render_template('management/privacy_dashboard.html', self.category,
                                                    'privacy_dashboard', **kwargs)
