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

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.events.features.base import EventFeature
from indico.modules.events.layout.default import DEFAULT_MENU_ENTRIES
from indico.modules.events.settings import EventSettingsProxy
from indico.util.i18n import _
from indico.web.flask.util import url_for


logger = Logger.get('events.layout')
layout_settings = EventSettingsProxy('layout', {
    'is_searchable': True,
    'show_nav_bar': True,
    'show_social_badges': True,
    'show_banner': False,
    'header_text_color': '',
    'header_background_color': '',
    'announcement': None,
    'show_announcement': False
    # TODO: handle style sheets
})


@signals.event_management.sidemenu_advanced.connect
def _extend_event_management_menu_layout(event, **kwargs):
    from MaKaC.webinterface.wcomponents import SideMenuItem
    can_modify = event.canModify(session.user)
    yield 'layout', SideMenuItem(_('Layout'), url_for('event_layout.index', event), visible=can_modify)
    yield 'menu', SideMenuItem(_('Menu'), url_for('event_layout.menu', event), visible=can_modify)
    yield 'images', SideMenuItem(_('Images'), url_for('event_layout.images', event), visible=can_modify,
                                 event_feature='images')


@signals.event.sidemenu.connect
def _get_default_menu_entries(sender, **kwargs):
    for entry in DEFAULT_MENU_ENTRIES:
        yield entry


@signals.event_management.clone.connect
def _get_image_cloner(event, **kwargs):
    from indico.modules.events.layout.clone import ImageCloner
    return ImageCloner(event)


@signals.event.get_feature_definitions.connect
def _get_feature_definitions(sender, **kwargs):
    return ImagesFeature


class ImagesFeature(EventFeature):
    name = 'images'
    friendly_name = _('Image manager')
    description = _('Allows event managers to attach images to the event, which can then be used from HTML code. '
                    'Very useful for e.g. sponsor logos and conference custom pages.')

    @classmethod
    def is_default_for_event(cls, event):
        return event.getType() == 'conference'
