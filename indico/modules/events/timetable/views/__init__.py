# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import posixpath
from itertools import groupby

from flask import render_template, request

from indico.core import signals
from indico.modules.events.layout import get_theme_global_settings, theme_settings
from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.modules.events.timetable.util import get_nested_timetable, get_nested_timetable_location_conditions
from indico.modules.events.timetable.views.weeks import inject_week_timetable
from indico.modules.events.util import get_theme
from indico.modules.events.views import WPConferenceDisplayBase
from indico.util.mathjax import MathjaxMixin
from indico.util.signals import values_from_signal
from indico.web.flask.templating import register_template_hook, template_hook


register_template_hook('week-meeting-body', inject_week_timetable)


class WPManageTimetable(MathjaxMixin, WPEventManagement):
    template_prefix = 'events/timetable/'
    sidemenu_option = 'timetable'
    bundles = ('markdown.js', 'module_events.contributions.js')

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

    entries = get_nested_timetable(event, include_notes=True, show_date=show_date, show_session=show_session)
    show_siblings_location, show_children_location = get_nested_timetable_location_conditions(entries)
    days = [(day, list(e)) for day, e in groupby(entries, lambda e: e.start_dt.astimezone(event_tz).date())]
    theme_id = get_theme(event, view)[0]
    theme = theme_settings.themes[theme_id]
    plugin = theme.get('plugin')
    tpl_name = theme.get('tt_template', theme['template'])
    tt_tpl = ((plugin.name + tpl_name)
              if (plugin and tpl_name[0] == ':')
              else posixpath.join('events/timetable/display', tpl_name))
    multiple_days = event.start_dt.astimezone(event_tz).date() != event.end_dt.astimezone(event_tz).date()

    return render_template(tt_tpl, event=event, entries=entries, days=days,
                           timezone=event_tz.zone, tz_object=event_tz, hide_contribs=(detail_level == 'session'),
                           theme_settings=get_theme_global_settings(event, theme_id),
                           show_siblings_location=show_siblings_location, show_children_location=show_children_location,
                           multiple_days=multiple_days, **kwargs)


def _entry_title_key(entry) -> tuple[str, str]:
    obj = entry.object
    if entry.type == TimetableEntryType.SESSION_BLOCK:
        return (obj.session.code, obj.full_title)
    return ('', obj.title)
