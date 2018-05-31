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

from datetime import timedelta

from celery.schedules import crontab
from celery.signals import beat_init, import_modules
from flask import render_template, session

import indico
from indico.core import signals
from indico.core.celery.core import IndicoCelery
from indico.core.config import config
from indico.core.db import db
from indico.core.settings import SettingsProxy
from indico.core.settings.converters import DatetimeConverter
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.flask.templating import template_hook
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('celery',)


#: The Celery instance for all Indico tasks
celery = IndicoCelery('indico')


celery_settings = SettingsProxy('celery', {
    'last_ping': None,
    'last_ping_version': None
}, converters={
    'last_ping': DatetimeConverter
})


@signals.app_created.connect
def _load_default_modules(app, **kwargs):
    celery.loader.import_default_modules()  # load all tasks


@import_modules.connect
def _import_modules(*args, **kwargs):
    import indico.core.emails
    import indico.util.tasks
    signals.import_tasks.send()


@beat_init.connect
def _send_initial_heartbeat(*args, **kwargs):
    heartbeat.delay(initial=True)


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        return SideMenuItem('celery', _("Tasks"), url_for('celery.index'), 20, icon='time')


@template_hook('global-announcement', priority=-100)
def _inject_announcement_header(**kwargs):
    if not session.user or not session.user.is_admin or config.DISABLE_CELERY_CHECK:
        return
    last_ping = celery_settings.get('last_ping')
    last_ping_version = celery_settings.get('last_ping_version')
    down = not last_ping or (now_utc() - last_ping) > timedelta(hours=1)
    mismatch = last_ping_version and last_ping_version != indico.__version__
    if down or mismatch:
        return render_template('celery/warning.html', down=down)


@celery.periodic_task(name='heartbeat', run_every=crontab(minute='*/30'))
def heartbeat(initial=False):
    celery_settings.set('last_ping', now_utc())
    if initial:
        celery_settings.set('last_ping_version', indico.__version__)
    db.session.commit()
