# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from indico.core import signals
from indico.core.logger import Logger
from indico.core.settings import SettingsProxy
from indico.core.settings.converters import ModelListConverter
from indico.modules.categories.models.categories import Category


logger = Logger.get('rb')


rb_settings = SettingsProxy('roombooking', {
    'excluded_categories': [],
    'notification_before_days': 2,
    'notification_before_days_weekly': 5,
    'notification_before_days_monthly': 7,
    'notifications_enabled': True,
    'end_notification_daily': 1,
    'end_notification_weekly': 3,
    'end_notification_monthly': 7,
    'end_notifications_enabled': True,
    'booking_limit': 365,
    'tileserver_url': None,
    'grace_period': None,
}, acls={
    'admin_principals',
    'authorized_principals'
}, converters={
    'excluded_categories': ModelListConverter(Category)
})


@signals.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.rb.tasks
