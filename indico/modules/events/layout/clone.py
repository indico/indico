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

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.events.cloning import EventCloner
from indico.modules.events.features.util import is_feature_enabled
from indico.modules.events.layout import layout_settings
from indico.modules.events.layout.models.menu import MenuEntry, EventPage
from indico.modules.events.models.events import EventType
from indico.util.i18n import _


class ImageCloner(EventCloner):
    name = 'images'
    friendly_name = _('Images')

    @property
    def is_visible(self):
        return is_feature_enabled(self.old_event, 'images')

    @property
    def is_available(self):
        return bool(self._find_images().count())

    def _find_images(self):
        return self.old_event.layout_images

    def run(self, new_event, cloners, shared_data):
        from indico.modules.events.layout.models.images import ImageFile
        for old_image in self._find_images():
            new_image = ImageFile(filename=old_image.filename, content_type=old_image.content_type)
            new_event.layout_images.append(new_image)
            with old_image.open() as fd:
                new_image.save(fd)
            db.session.flush()


class LayoutCloner(EventCloner):
    name = 'layout'
    friendly_name = _('Layout settings and menu customization')

    @property
    def is_visible(self):
        return self.old_event.type_ == EventType.conference

    def run(self, new_event, cloners, shared_data):
        for col in ('logo_metadata', 'logo', 'stylesheet_metadata', 'stylesheet'):
            setattr(new_event, col, getattr(self.old_event, col))

        layout_settings.set_multi(new_event, layout_settings.get_all(self.old_event, no_defaults=True))
        if layout_settings.get(self.old_event, 'use_custom_menu'):
            for menu_entry in MenuEntry.get_for_event(self.old_event):
                self._copy_menu_entry(menu_entry, new_event, new_event.menu_entries)
        db.session.flush()

    def _copy_menu_entry(self, menu_entry, new_event, container, include_children=True):
        base_columns = get_simple_column_attrs(MenuEntry)
        new_menu_entry = MenuEntry(**{col: getattr(menu_entry, col) for col in base_columns})
        if menu_entry.is_page:
            with db.session.no_autoflush:  # menu_entry.page is lazy-loaded
                page = EventPage(event_new=new_event, html=menu_entry.page.html)
            new_menu_entry.page = page
            if menu_entry.page.is_default:
                new_event.default_page = new_menu_entry.page
        container.append(new_menu_entry)
        if include_children:
            for child in menu_entry.children:
                self._copy_menu_entry(child, new_event, new_menu_entry.children, include_children=False)
