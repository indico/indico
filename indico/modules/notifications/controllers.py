# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, redirect, session

from indico.core.logger import Logger
from indico.modules.admin import RHAdminBase
from indico.modules.notifications import settings
from indico.modules.notifications.forms import NotificationSettingsForm
from indico.modules.notifications.util import make_notification, process_notification
from indico.modules.notifications.views import WPNotificationSettings
from indico.util.i18n import _
from indico.web.flask.util import jsonify_data, url_for
from indico.web.forms.base import FormDefaults


logger = Logger.get('notifications')


class RHNotificationsAdmin(RHAdminBase):
    def _process(self):
        form = NotificationSettingsForm(obj=FormDefaults(**settings.get_all()))
        if form.validate_on_submit():
            settings.set_multi(form.data)
            logger.info('Notification settings updated by %s', session.user)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.admin'))
        return WPNotificationSettings.render_template('admin.html', form=form, settings=settings)


class RHSendTestMessage(RHAdminBase):
    def _process(self):
        process_notification(
            make_notification({session.user}, subject='TEST', body='This is a test message!', content_type='markdown')
        )
        flash(_('Test Message sent!'), 'success')
        return jsonify_data(flash=True)
