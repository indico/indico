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

import posixpath
from operator import attrgetter

from flask import render_template, request, session
from pytz import timezone
from sqlalchemy.orm import joinedload

from indico.modules.events.layout import theme_settings
from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.web.flask.templating import template_hook

from MaKaC.common.timezoneUtils import DisplayTZ
from MaKaC.webinterface.pages.base import WPJinjaMixin
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase, WPConferenceDefaultDisplayBase


class WPManageTimetable(WPJinjaMixin, WPConferenceModifBase):
    template_prefix = 'events/timetable/'
    sidemenu_option = 'timetable'

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + self._asset_env['modules_timetable_js'].urls()

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + self._asset_env['timetable_sass'].urls()


class WPDisplayTimetable(WPJinjaMixin, WPConferenceDefaultDisplayBase):
    template_prefix = 'events/timetable/'
    menu_entry_name = 'timetable'

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + self._asset_env['modules_timetable_js'].urls()

    def getCSSFiles(self):
        return WPConferenceDefaultDisplayBase.getCSSFiles(self) + self._asset_env['timetable_sass'].urls()


@template_hook('meeting-body')
def _inject_meeting_body(event, **kwargs):
    event_tz_name = DisplayTZ(session.user, event.as_legacy).getDisplayTZ()
    event_tz = timezone(event_tz_name)
    show_date = request.args.get('showDate', 'all')
    show_session = request.args.get('showSession', 'all')
    detail_level = request.args.get('detailLevel', 'contribution')
    view = request.args.get('view')

    children_strategy = joinedload('children')
    children_strategy.joinedload('session_block').joinedload('*')
    children_strategy.joinedload('break_')

    children_contrib_strategy = children_strategy.joinedload('contribution')
    children_contrib_strategy.joinedload('*'),
    children_contrib_strategy.joinedload('subcontributions')
    children_contrib_strategy.lazyload('attachment_folders')

    children_subcontrib_strategy = children_contrib_strategy.joinedload('subcontributions')
    children_subcontrib_strategy.joinedload('*')
    children_subcontrib_strategy.lazyload('attachment_folders')

    contrib_strategy = joinedload('contribution')
    contrib_strategy.joinedload('*')
    contrib_strategy.joinedload('subcontributions')
    contrib_strategy.lazyload('attachment_folders')

    # try to minimize the number of DB queries
    options = [contrib_strategy,
               children_strategy,
               joinedload('session_block').joinedload('*'),
               joinedload('break_')]

    entries = []
    for entry in event.timetable_entries.filter_by(parent=None).options(*options):
        if show_date != 'all' and entry.start_dt.astimezone(event_tz).date().isoformat() != show_date:
            continue
        if entry.type == TimetableEntryType.CONTRIBUTION and (detail_level != 'contribution' or show_session != 'all'):
            continue
        elif (entry.type == TimetableEntryType.SESSION_BLOCK and show_session != 'all' and
                unicode(entry.object.session.id) != show_session):
            continue

        if entry.type == TimetableEntryType.BREAK:
            entries.append(entry)
        elif entry.object.can_access(session.user):
            entries.append(entry)

    entries.sort(key=attrgetter('end_dt'), reverse=True)
    entries.sort(key=lambda entry: (entry.start_dt, entry.object.title if entry.object else entry.title))

    days = sorted({entry.start_dt.astimezone(event_tz).date() for entry in entries})
    theme_id = view or event.theme
    theme = theme_settings.themes[theme_id]
    tt_tpl = theme.get('tt_template', theme['template'])

    return render_template(posixpath.join('events/timetable/display', tt_tpl), event=event, entries=entries, days=days,
                           timezone=event_tz_name, tz_object=event_tz, hide_contribs=(detail_level == 'session'),
                           show_notes=(theme_id == 'standard_inline_minutes'), theme_settings=theme.get('settings', {}))
