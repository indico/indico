# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import render_template
from markupsafe import Markup

from indico.core import signals
from indico.util.signals import named_objects_from_signal
from indico.util.string import format_repr


class _MenuSectionBase:
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
    """Define a side menu section (item set).

    :param name: the unique name of the section
    :param title: the title of the section (displayed)
    :param weight: the "weight" (higher means it shows up first)
    :param active: whether the section should be shown expanded by default
    :param icon: icon that will be displayed next to the section title.
    """

    def __init__(self, name, title, weight=-1, active=False, icon=None):
        super().__init__(name, title, weight)
        self._active = active
        self.icon = 'icon-' + icon if icon else None

    @property
    def active(self):
        return self._active or any(item.active for item in self._items)

    def __repr__(self):
        return format_repr(self, 'name', 'title', active=False)


class SideMenuItem:
    """Define a side menu item.

    :param name: the unique name (within the menu) of the item
    :param title: the title of the menu item (displayed)
    :param url: the URL that the link will point to
    :param weight: the "weight" (higher means it shows up first)
    :param active: whether the item will be shown as active by default
    :param disabled: if `True`, the item will be displayed as disabled
    :param section: section the item will be put in
    :param icon: icon that will be displayed next to the item
    :param badge: text (typically a number) that is shown in a badge
    """

    is_section = False

    def __init__(self, name, title, url, weight=-1, active=False, disabled=False, section=None, icon=None,
                 sui_icon=None, badge=None):
        assert not (icon and sui_icon)
        self.name = name
        self.title = title
        self.url = url
        self.active = active
        self.disabled = disabled
        self.section = section
        self.weight = weight
        self.icon = ('icon-' + icon) if icon else None
        self.sui_icon = sui_icon
        self.badge = badge

    def __repr__(self):
        return format_repr(self, 'name', 'title', 'url', active=False, disabled=False)


class TopMenuSection(_MenuSectionBase):
    """Define a top menu section (dropdown).

    :param name: the unique name of the section
    :param title: the title of the section (displayed)
    :param weight: the "weight" (higher means it shows up first)
    """

    def __repr__(self):
        return format_repr(self, 'name', 'title')


class TopMenuItem:
    """Define a top menu item.

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

    for id_, section in named_objects_from_signal(signals.menu.sections.send(menu_id, **kwargs)).items():
        sections[id_] = section
        top_level.add(section)

    for id_, item in named_objects_from_signal(signals.menu.items.send(menu_id, **kwargs)).items():
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
