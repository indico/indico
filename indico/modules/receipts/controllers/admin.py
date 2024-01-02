# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, redirect

from indico.modules.admin.controllers.base import RHAdminBase
from indico.modules.receipts.forms import ReceiptsSettingsForm
from indico.modules.receipts.settings import receipts_settings
from indico.modules.receipts.views import WPReceiptsAdmin
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHGlobalReceiptsSettings(RHAdminBase):
    """Manage global settings for the receipts module in the server admin area."""

    def _process(self):
        form = ReceiptsSettingsForm(obj=FormDefaults(**receipts_settings.get_all()))
        if form.validate_on_submit():
            receipts_settings.set_multi(form.data)
            flash(_('Settings have been saved'), 'success')
            return redirect(url_for('.admin_settings'))
        return WPReceiptsAdmin.render_template('admin_settings.html', 'receipts', form=form)
