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

from celery.signals import import_modules
from flask import session

from indico.core import signals
from indico.core.celery.core import IndicoCelery
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('celery',)


#: The Celery instance for all Indico tasks
celery = IndicoCelery('indico')


@signals.app_created.connect
def _load_default_modules(app, **kwargs):
    celery.loader.import_default_modules()  # load all tasks


@import_modules.connect
def _import_modules(*args, **kwargs):
    import indico.core.emails
    import indico.util.tasks
    signals.import_tasks.send()


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        return SideMenuItem('celery', _("Tasks"), url_for('celery.index'), 20, icon='time')
