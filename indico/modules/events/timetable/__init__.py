# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.timetable')


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.can_manage(session.user, allow_key=True):
        return
    return SideMenuItem('timetable', _('Timetable'), url_for('timetable.timetable', event), weight=80, icon='calendar')


@signals.event_management.get_cloners.connect
def _get_timetable_cloner(sender, **kwargs):
    from indico.modules.events.timetable.clone import TimetableCloner
    return TimetableCloner
