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

from __future__ import absolute_import, unicode_literals

from flask import render_template
from markupsafe import Markup

from indico.core import signals
from indico.util.signals import named_objects_from_signal
from indico.util.string import format_repr, return_ascii


class _MenuSectionBase(object):
    is_section = True

    def __init__(self, name, title, weight=-1):
        self.name = name
        self.title = title
        self.weight = weight
        self._items = set()
        self._sorted_items = None

    def add_item(self, item):
        self._sorted_items = None
        self._items.add(item)

    @property
    def items(self):
        if self._sorted_items is None:
            self._sorted_items = sorted(self._items, key=lambda x: (-x.weight, x.title.lower()))
        return self._sorted_items


class SideMenuSection(_MenuSectionBase):
    """Defines a side menu section (item set).

    :param name: the unique name of the section
    :param title: the title of the section (displayed)
    :param weight: the "weight" (higher means it shows up first)
    :param active: whether the section should be shown expanded by default
    :param icon: icon that will be displayed next to the section title.
    """

    def __init__(self, name, title, weight=-1, active=False, icon=None):
        super(SideMenuSection, self).__init__(name, title, weight)
        self._active = active
        self.icon = 'icon-' + icon if icon else None

    @property
    def active(self):
        return self._active or any(item.active for item in self._items)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'name', 'title', active=False)


class SideMenuItem(object):
    """Defines a side menu item.

    :param name: the unique name (within the menu) of the item
    :param title: the title of the menu item (displayed)
    :param url: the URL that the link will point to
    :param weight: the "weight" (higher means it shows up first)
    :param active: whether the item will be shown as active by default
    :param disabled: if `True`, the item will be displayed as disabled
    :param section: section the item will be put in
    :param icon: icon that will be displayed next to the item
    """

    is_section = False

    def __init__(self, name, title, url, weight=-1, active=False, disabled=False, section=None, icon=None):
        self.name = name
        self.title = title
        self.url = url
        self.active = active
        self.disabled = disabled
        self.section = section
        self.weight = weight
        self.icon = ('icon-' + icon) if icon else None

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'name', 'title', 'url', active=False, disabled=False)


class TopMenuSection(_MenuSectionBase):
    """Defines a top menu section (dropdown).

    :param name: the unique name of the section
    :param title: the title of the section (displayed)
    :param weight: the "weight" (higher means it shows up first)
    """

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'name', 'title')


class TopMenuItem(object):
    """Defines a top menu item.

    :param name: the unique name (within the menu) of the item
    :param title: the title of the menu item (displayed)
    :param url: the URL that the link will point to
    :param weight: the "weight" (higher means it shows up first)
    :param section: dropdown section the item will be put in
    """

    is_section = False

    def __init__(self, name, title, url, weight=-1, section=None):
        self.name = name
        self.title = title
        self.url = url
        self.section = section
        self.weight = weight

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'name', 'title', 'url')


def build_menu_structure(menu_id, active_item=None, **kwargs):
    """Build a menu (list of entries) with sections/items.

    Information is provided by specific signals and filtered
    by menu id.
    This can be used as a very thin framework for menu
    handling across the app.

    :param menu_id: menu_id used to filter out signal calls
    :param active_item: ID of currently active menu item
    :param kwargs: extra arguments passed to the signals
    :return: properly sorted list (taking weights into account)
    """
    top_level = set()
    sections = {}

    for id_, section in named_objects_from_signal(signals.menu.sections.send(menu_id, **kwargs)).iteritems():
        sections[id_] = section
        top_level.add(section)

    for id_, item in named_objects_from_signal(signals.menu.items.send(menu_id, **kwargs)).iteritems():
        if id_ == active_item:
            item.active = True
        if item.section is None:
            top_level.add(item)
        else:
            sections[item.section].add_item(item)

    return sorted(top_level, key=lambda x: (-x.weight, x.title))


def get_menu_item(menu_id, item, **kwargs):
    """Get a specific menu item.

    :param menu_id: menu_id used to filter out signal calls
    :param item: ID of the item to retrieve
    :param kwargs: extra arguments passed to the signals
    :return: the specified menu item or ``None``
    """
    return named_objects_from_signal(signals.menu.items.send(menu_id, **kwargs)).get(item)


def render_sidemenu(menu_id, active_item=None, **kwargs):
    """Render a sidemenu with sections/items.

    :param menu_id: The identifier of the menu.
    :param active_item: The name of the currently-active menu item.
    :param kwargs: Additional arguments passed to the menu signals.
    """
    items = build_menu_structure(menu_id, active_item=active_item, **kwargs)
    return Markup(render_template('side_menu.html', items=items, menu_id=menu_id))
