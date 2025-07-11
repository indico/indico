# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, redirect, session

from indico.modules.admin import RHAdminBase
from indico.modules.announcement import announcement_settings
from indico.modules.announcement.forms import AnnouncementForm
from indico.modules.announcement.views import WPAnnouncement
from indico.modules.logs import AppLogEntry, AppLogRealm, LogKind
from indico.modules.logs.util import make_diff_log
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHAnnouncement(RHAdminBase):
    def _log_changes(self, changes):
        log_fields = {
            'enabled': 'Enabled',
            'message': 'Message',
        }
        AppLogEntry.log(AppLogRealm.admin, LogKind.change, 'Announcement', 'Data updated', session.user,
                        data={'Changes': make_diff_log(changes, log_fields)})

    def _process(self):
        current_settings = announcement_settings.get_all()
        form = AnnouncementForm(obj=FormDefaults(**current_settings))
        if form.validate_on_submit():
            changes = {k: (current_settings[k], v) for k, v in form.data.items() if current_settings[k] != v}
            self._log_changes(changes)
            announcement_settings.set_multi(form.data)
            flash(_('Settings have been saved'), 'success')
            return redirect(url_for('announcement.manage'))
        return WPAnnouncement.render_template('settings.html', 'announcement', form=form)
