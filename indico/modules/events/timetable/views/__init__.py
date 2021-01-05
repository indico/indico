# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import posixpath
from itertools import groupby
from operator import attrgetter

from flask import render_template, request, session
from sqlalchemy.orm import joinedload

from indico.core import signals
from indico.modules.events.layout import theme_settings
from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.modules.events.timetable.views.weeks import inject_week_timetable
from indico.modules.events.util import get_theme
from indico.modules.events.views import WPConferenceDisplayBase
from indico.util.signals import values_from_signal
from indico.web.flask.templating import register_template_hook, template_hook


register_template_hook('week-meeting-body', inject_week_timetable)


class WPManageTimetable(WPEventManagement):
    template_prefix = 'events/timetable/'
    sidemenu_option = 'timetable'
    bundles = ('module_events.contributions.js',)

    def __init__(self, rh, event_, **kwargs):
        custom_links = dict(values_from_signal(signals.event.timetable_buttons.send(self)))
        WPEventManagement.__init__(self, rh, event_, custom_links=custom_links, **kwargs)


class WPDisplayTimetable(WPConferenceDisplayBase):
    template_prefix = 'events/timetable/'
    menu_entry_name = 'timetable'


@template_hook('meeting-body')
def inject_meeting_body(event, **kwargs):
    event.preload_all_acl_entries()
    event_tz = event.display_tzinfo
    show_date = request.args.get('showDate') or 'all'
    show_session = request.args.get('showSession') or 'all'
    detail_level = request.args.get('detailLevel') or 'contribution'
    view = request.args.get('view')

    children_strategy = joinedload('children')
    children_strategy.joinedload('session_block').joinedload('person_links')
    children_strategy.joinedload('break_')

    children_contrib_strategy = children_strategy.subqueryload('contribution')
    children_contrib_strategy.joinedload('person_links')
    children_contrib_strategy.joinedload('subcontributions')
    children_contrib_strategy.joinedload('references')
    children_contrib_strategy.joinedload('own_room')
    children_contrib_strategy.joinedload('note')

    children_subcontrib_strategy = children_contrib_strategy.joinedload('subcontributions')
    children_subcontrib_strategy.joinedload('person_links')
    children_subcontrib_strategy.joinedload('references')

    contrib_strategy = joinedload('contribution')
    contrib_strategy.joinedload('person_links')
    contrib_strategy.joinedload('references')
    contrib_strategy.joinedload('note')

    subcontrib_strategy = contrib_strategy.joinedload('subcontributions')
    subcontrib_strategy.joinedload('person_links')
    subcontrib_strategy.joinedload('references')
    subcontrib_strategy.joinedload('note')

    # try to minimize the number of DB queries
    options = [contrib_strategy,
               children_strategy,
               joinedload('session_block').joinedload('person_links'),
               joinedload('session_block').joinedload('own_room'),
               joinedload('break_')]

    entries = []
    show_siblings_location = False
    show_children_location = {}
    for entry in event.timetable_entries.filter_by(parent=None).options(*options):
        if show_date != 'all' and entry.start_dt.astimezone(event_tz).date().isoformat() != show_date:
            continue
        if (entry.type == TimetableEntryType.CONTRIBUTION and
                (detail_level not in ('contribution', 'all') or show_session != 'all')):
            continue
        elif (entry.type == TimetableEntryType.SESSION_BLOCK and show_session != 'all' and
                unicode(entry.object.session.friendly_id) != show_session):
            continue

        if entry.type == TimetableEntryType.BREAK:
            entries.append(entry)
        elif entry.object.can_access(session.user):
            entries.append(entry)
        if not entry.object.inherit_location:
            show_siblings_location = True
        show_children_location[entry.id] = not all(child.object.inherit_location for child in entry.children)

    entries.sort(key=attrgetter('end_dt'), reverse=True)
    entries.sort(key=lambda entry: (entry.start_dt, _entry_title_key(entry)))

    days = [(day, list(e)) for day, e in groupby(entries, lambda e: e.start_dt.astimezone(event_tz).date())]
    theme = theme_settings.themes[get_theme(event, view)[0]]
    plugin = theme.get('plugin')
    tpl_name = theme.get('tt_template', theme['template'])
    tt_tpl = ((plugin.name + tpl_name)
              if (plugin and tpl_name[0] == ':')
              else posixpath.join('events/timetable/display', tpl_name))
    multiple_days = event.start_dt.astimezone(event_tz).date() != event.end_dt.astimezone(event_tz).date()
    return render_template(tt_tpl, event=event, entries=entries, days=days,
                           timezone=event_tz.zone, tz_object=event_tz, hide_contribs=(detail_level == 'session'),
                           theme_settings=theme.get('settings', {}), show_siblings_location=show_siblings_location,
                           show_children_location=show_children_location, multiple_days=multiple_days, **kwargs)


def _entry_title_key(entry):
    obj = entry.object
    return obj.full_title if entry.type == TimetableEntryType.SESSION_BLOCK else obj.title
