# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.core import signals
from indico.core.celery.core import IndicoCelery
from indico.util.i18n import _
from indico.web.flask.util import url_for

__all__ = ('celery',)


#: The Celery instance for all Indico tasks
celery = IndicoCelery('indico')


@signals.app_created.connect
def _load_default_modules(app, **kwargs):
    celery.loader.import_default_modules()  # load all tasks


@import_modules.connect
def _import_modules(*args, **kwargs):
    signals.import_tasks.send()


@signals.admin_sidemenu.connect
def _extend_admin_menu(sender, **kwargs):
    from MaKaC.webinterface.wcomponents import SideMenuItem
    return 'celery', SideMenuItem(_("Tasks"), url_for('celery.index'))
