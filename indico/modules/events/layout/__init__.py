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

import os

from flask import session
from jinja2.filters import do_filesizeformat

import indico
from indico.core import signals
from indico.core.logger import Logger
from indico.modules.events.features.base import EventFeature
from indico.modules.events.logs import EventLogKind, EventLogRealm
from indico.modules.events.models.events import EventType
from indico.modules.events.settings import EventSettingsProxy, ThemeSettingsProxy
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.layout')
layout_settings = EventSettingsProxy('layout', {
    'is_searchable': True,
    'show_nav_bar': True,
    'show_social_badges': True,
    'show_banner': False,
    'header_text_color': '',
    'header_background_color': '',
    'announcement': None,
    'show_announcement': False,
    'use_custom_css': False,
    'theme': None,
    'timetable_theme': None,  # meetings/lectures
    'use_custom_menu': False,
    'timetable_by_room': False,
    'timetable_detailed': False
})

theme_settings = ThemeSettingsProxy(os.path.join(os.path.dirname(indico.__file__), 'modules', 'events', 'themes.yaml'))


@signals.event.type_changed.connect
def _event_type_changed(event, **kwargs):
    layout_settings.delete(event, 'timetable_theme')


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu_layout(sender, event, **kwargs):
    if not event.can_manage(session.user):
        return
    if event.as_legacy.getType() == 'conference':
        yield SideMenuItem('layout', _('Layout'), url_for('event_layout.index', event), section='customization')
        yield SideMenuItem('menu', _('Menu'), url_for('event_layout.menu', event), section='customization')
    if event.has_feature('images'):
        yield SideMenuItem('images', _('Images'), url_for('event_layout.images', event), section='customization')


@signals.event.sidemenu.connect
def _get_default_menu_entries(sender, **kwargs):
    from indico.modules.events.layout.default import get_default_menu_entries
    for entry in get_default_menu_entries():
        yield entry


@signals.event.cloned.connect
def _event_cloned(old_event, new_event, **kwargs):
    if old_event.as_legacy.getType() == 'conference':
        return
    # for meetings/lecture we want to keep the default timetable style in all cases
    theme = layout_settings.get(old_event, 'timetable_theme')
    if theme is not None:
        layout_settings.set(new_event, 'timetable_theme', theme)


@signals.event_management.get_cloners.connect
def _get_cloners(sender, **kwargs):
    from indico.modules.events.layout.clone import ImageCloner, LayoutCloner
    yield ImageCloner
    yield LayoutCloner


@signals.event.get_feature_definitions.connect
def _get_feature_definitions(sender, **kwargs):
    return ImagesFeature


@signals.event_management.image_created.connect
def _log_image_created(image, user, **kwargs):
    image.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Layout',
                        'Added image "{}"'.format(image.filename), user, data={
                            'File name': image.filename,
                            'File type': image.content_type,
                            'File size': do_filesizeformat(image.size)
                        })


@signals.event_management.image_deleted.connect
def _log_image_deleted(image, user, **kwargs):
    image.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Layout',
                        'Deleted image "{}"'.format(image.filename), user, data={
                            'File name': image.filename
                        })


class ImagesFeature(EventFeature):
    name = 'images'
    friendly_name = _('Image manager')
    description = _('Allows event managers to attach images to the event, which can then be used from HTML code. '
                    'Very useful for e.g. sponsor logos and conference custom pages.')

    @classmethod
    def is_default_for_event(cls, event):
        return event.type_ == EventType.conference
