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

from flask import render_template, session

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.flask.templating import template_hook
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.timetable')


@signals.event.sidemenu.connect
def _extend_event_menu(sender, **kwargs):
    from indico.modules.events.layout.util import MenuEntryData
    yield MenuEntryData(title=_("Timetable"), name='timetable', endpoint='timetable.timetable', position=3,
                        static_site=True)


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    from indico.modules.events.sessions.util import can_manage_sessions
    if not can_manage_sessions(session.user, event, 'ANY'):
        return
    if event.type != 'lecture':
        return SideMenuItem('timetable', _('Timetable'), url_for('timetable.management', event), weight=80,
                            icon='calendar')


@signals.event_management.get_cloners.connect
def _get_timetable_cloner(sender, **kwargs):
    from indico.modules.events.timetable.clone import TimetableCloner
    return TimetableCloner


@template_hook('session-timetable')
def _render_session_timetable(session, **kwargs):
    from indico.modules.events.timetable.util import render_session_timetable
    return render_session_timetable(session, **kwargs)


@template_hook('now-happening')
def _render_now_happening_info(event, text_color_css, **kwargs):
    from indico.modules.events.layout import layout_settings
    if layout_settings.get(event, 'show_banner'):
        current_dt = now_utc(exact=False)
        entries = event.timetable_entries.filter(TimetableEntry.start_dt <= current_dt,
                                                 TimetableEntry.end_dt > current_dt,
                                                 TimetableEntry.type != TimetableEntryType.SESSION_BLOCK).all()
        if not entries:
            return
        return render_template('events/display/now_happening.html', event=event, entries=entries,
                               text_color_css=text_color_css)
