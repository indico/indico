# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime

from flask import flash, redirect

from indico.modules.admin import RHAdminBase
from indico.modules.announcement import announcement_settings
from indico.modules.announcement.forms import AnnouncementForm
from indico.modules.announcement.views import WPAnnouncement
from indico.util.date_time import server_to_utc
# from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHAnnouncement(RHAdminBase):
    def _process(self):
        form = AnnouncementForm(obj=FormDefaults(**announcement_settings.get_all(),
                                                 test_start_dt=server_to_utc(datetime(2025, 4, 8, 13, 37))))
        if form.validate_on_submit():
            # announcement_settings.set_multi(form.data)
            # flash(_('Settings have been saved'), 'success')
            flash(f'{form.test_start_dt.data} - {form.test_end_dt.data}', 'info')
            return redirect(url_for('announcement.manage'))
        return WPAnnouncement.render_template('settings.html', 'announcement', form=form)
