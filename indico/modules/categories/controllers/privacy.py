# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, redirect

from indico.modules.categories.controllers.base import RHManageCategoryBase
from indico.modules.categories.forms import CategoryPrivacyForm
from indico.modules.categories.operations import get_category_privacy, update_category_privacy
from indico.modules.categories.views import WPCategoryManagement
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHCategoryPrivacy(RHManageCategoryBase):
    """Show category privacy dashboard."""

    def _process(self):
        privacy_settings, inherited = get_category_privacy(self.category)
        lock_privacy_settings = False
        if inherited:
            lock_privacy_settings = bool(privacy_settings.get('lock_privacy_data'))
        form = CategoryPrivacyForm(obj=FormDefaults(**privacy_settings), category=self.category)
        if form.validate_on_submit():
            if lock_privacy_settings:
                flash(_('The privacy settings is locked in a parent category and cannot be modified here.'), 'error')
                return redirect(url_for('.manage_privacy_dashboard', self.category))
            update_category_privacy(self.category, form.data)
            flash(_('Privacy settings have been updated'), 'success')
            return redirect(url_for('.manage_privacy_dashboard', self.category))
        return WPCategoryManagement.render_template('management/privacy_dashboard.html', self.category,
                                                    'privacy_dashboard', form=form, inherited=inherited,
                                                    lock_privacy_settings=lock_privacy_settings)
