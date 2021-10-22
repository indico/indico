# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, redirect
from werkzeug.exceptions import Forbidden

from indico.core.config import config
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.management.forms import PrivacyDashboardForm
from indico.modules.events.management.settings import privacy_settings
from indico.modules.events.management.views import WPEventPrivacy
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHEventPrivacy(RHManageEventBase):
    """Show event privacy dashboard."""

    def _process(self):
        form = PrivacyDashboardForm(obj=FormDefaults(**privacy_settings.get_all(self.event)), event=self.event)
        if form.validate_on_submit():
            privacy_settings.set_multi(self.event, form.data)
            flash(_('Privacy settings have been updated'), 'success')
            return redirect(url_for('.privacy_dashboard', self.event))
        return WPEventPrivacy.render_template('privacy_dashboard.html', self.event, 'privacy_dashboard', form=form)

    def _check_access(self):
        RHManageEventBase._check_access(self)
        if not config.ENABLE_PRIVACY_DASHBOARD:
            raise Forbidden(_('The Privacy dashboard feature is disabled.'))
