# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict
from dataclasses import dataclass
from itertools import chain, count

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, load_only
from werkzeug.urls import url_parse

import indico
from indico.core import signals
from indico.core.cache import make_scoped_cache
from indico.core.config import config
from indico.core.db import db
from indico.core.plugins import url_for_plugin
from indico.modules.events.layout import layout_settings
from indico.modules.events.layout.models.menu import MenuEntry, MenuEntryType, TransientMenuEntry
from indico.util.caching import memoize_request
from indico.util.signals import named_objects_from_signal, values_from_signal
from indico.util.string import crc32
from indico.web.flask.util import url_for


_cache = make_scoped_cache('updated-menus')


def _menu_entry_key(entry_data):
    return entry_data.position == -1, entry_data.position, entry_data.name


@memoize_request
def get_menu_entries_from_signal():
    return named_objects_from_signal(signals.event.sidemenu.send(), plugin_attr='plugin')


def build_menu_entry_name(name, plugin=None):
    """Build the proper name for a menu entry.

    Given a menu entry's name and optionally a plugin, returns the
    correct name of the menu entry.

    :param name: str -- The name of the menu entry.
    :param plugin: IndicoPlugin or str -- The plugin (or the name of the
        plugin) which created the entry.
    """
    if plugin:
        plugin = getattr(plugin, 'name', plugin)
        return f'{plugin}:{name}'
    else:
        return name


class MenuEntryData:
    """Container to transmit menu entry-related data via signals.

    The data contained is transmitted via the `sidemenu` signal and used
    to build the side menu of an event.

    :param title: str -- The title of the menu, displayed to the user.
        The title should be translated using the normal gettext
        function, i.e. ``_('...')``, or the plugin's bound gettext
        function.
    :param name: str -- Name used to refer to the entry internally.
        This is never shown to the user. The name must be unique,
        names from plugins are automatically prefixed with the plugin
        name and a colon and therefore have to be unique only within the
        plugin. To mark the entry as active, its name must be specified
        in the `menu_entry_name` class attribute of the WP class. For
        plugins, the plugin name must be specified via the
        `menu_entry_plugin` attribute as well.
    :param endpoint: str -- The endpoint the entry will point to.
    :param position: int -- The desired position of the menu entry.
        the position is indicative only, relative to the other entries
        and not the exact position. Entries with the same position will
        be sorted alphanumerically on their name. A position of `-1`
        will append the entry at the end of the menu.
    :param is_enabled: bool -- Whether the entry should be enabled by
        default (Default: `True`).
    :param visible: function -- Determines if the entry should be
        visible. This is a simple function which takes only the `event`
        as parameter and returns a boolean to indicate if the entry is
        visible or not. It is called whenever the menu is displayed, so
        the current state of the event/user can be taken into account.
    :param parent: str -- The name of the parent entry (None for root
        entries).
    :param static_site: bool or str -- If True, this menu item should
        be shown in the menu of a static site.  When set to a string,
        the string will be used instead of a mangled version of the
        endpoint's URL.
    :param url_kwargs: dict -- Additional data passed to ``url_for``
        when building the url the menu item points to.
    """
    plugin = None

    def __init__(self, title, name, endpoint=None, position=-1, is_enabled=True, visible=None, parent=None,
                 static_site=False, url_kwargs=None, hide_if_restricted=True, new_tab=False):
        self.title = title
        self._name = name
        self.endpoint = endpoint
        self.position = position
        self._visible = visible
        self.is_enabled = is_enabled
        self.parent = parent
        self.static_site = static_site
        self.url_kwargs = url_kwargs or {}
        self.hide_if_restricted = hide_if_restricted
        self.new_tab = new_tab

    @property
    def name(self):
        return build_menu_entry_name(self._name, self.plugin)

    def visible(self, event):
        return self._visible(event) if self._visible else True

    def __repr__(self):
        parent = ''
        if self.parent:
            parent = f', parent={self.parent}'
        return f'<MenuEntryData({self.name}{parent}): "{self.title}">'


def _get_split_signal_entries():
    """Get the top-level and child menu entry data."""
    signal_entries = get_menu_entries_from_signal()
    top_data = {name: data
                for name, data in sorted(signal_entries.items(),
                                         key=lambda name_data: _menu_entry_key(name_data[1]))
                if not data.parent}
    child_data = defaultdict(list)
    for name, data in signal_entries.items():
        if data.parent is not None:
            child_data[data.parent].append(data)
    for parent, entries in child_data.items():
        entries.sort(key=_menu_entry_key)
    return top_data, child_data


def _get_menu_cache_data(event):
    from indico.core.plugins import plugin_engine
    cache_key = str(event.id)
    plugin_hash = crc32(','.join(sorted(plugin_engine.get_active_plugins())))
    cache_version = f'{indico.__version__}:{plugin_hash}'
    return cache_key, cache_version


def _menu_needs_recheck(event):
    """Check whether the menu needs to be checked for missing items."""
    cache_key, cache_version = _get_menu_cache_data(event)
    return _cache.get(cache_key) != cache_version


def _set_menu_checked(event):
    """Mark the menu as up to date."""
    cache_key, cache_version = _get_menu_cache_data(event)
    _cache.set(cache_key, cache_version)


def _save_menu_entries(entries):
    """Save new menu entries using a separate SA session."""
    with db.tmp_session() as sess:
        sess.add_all(entries)
        try:
            sess.commit()
        except IntegrityError as exc:
            # If there are two parallel requests trying to insert a new menu
            # item one of them will fail with an error due to the unique index.
            # If the IntegrityError involves that index, we assume it's just the
            # race condition and ignore it.
            sess.rollback()
            if 'ix_uq_menu_entries_event_id_name' not in str(exc):
                raise
            return False
        else:
            return True


def _rebuild_menu(event):
    """Create all menu entries in the database."""
    top_data, child_data = _get_split_signal_entries()
    pos_gen = count()
    entries = [_build_menu_entry(event, True, data, next(pos_gen), children=child_data.get(data.name))
               for name, data in top_data.items()]
    return _save_menu_entries(entries)


def _check_menu(event):
    """Create missing menu items in the database."""
    top_data, child_data = _get_split_signal_entries()

    query = (MenuEntry.query
             .filter(MenuEntry.event_id == int(event.id))
             .options(load_only('id', 'parent_id', 'name', 'position'),
                      joinedload('parent').load_only('id', 'parent_id', 'name', 'position'),
                      joinedload('children').load_only('id', 'parent_id', 'name', 'position')))

    existing = {entry.name: entry for entry in query}
    pos_gen = count(start=(max(x.position for x in existing.values() if not x.parent) + 1))
    entries = []
    top_created = set()
    for name, data in top_data.items():
        if name in existing:
            continue
        entries.append(_build_menu_entry(event, True, data, next(pos_gen), child_data.get(name)))
        top_created.add(name)

    child_pos_gens = {}
    for name, entry in existing.items():
        if entry.parent is not None:
            continue
        child_pos_gens[name] = count(start=(max(x.position for x in entry.children) + 1 if entry.children else 0))

    for parent_name, data_list in child_data.items():
        if parent_name in top_created:
            # adding a missing parent element also adds its children
            continue
        for data in data_list:
            if data.name in existing:
                continue
            parent = existing[parent_name]
            # use the parent id, not the object itself since we don't want to
            # connect the new objects here to the main sqlalchemy session
            entries.append(_build_menu_entry(event, True, data, next(child_pos_gens[parent.name]), parent_id=parent.id))

    return _save_menu_entries(entries)


def _build_menu(event):
    """Fetch the customizable menu data from the database."""
    entries = MenuEntry.get_for_event(event)
    if not entries:
        # empty menu, just build the whole structure without checking
        # for existing menu entries
        if _rebuild_menu(event):
            _set_menu_checked(event)
        return MenuEntry.get_for_event(event)
    elif _menu_needs_recheck(event):
        # menu items found, but maybe something new has been added
        if _check_menu(event):
            _set_menu_checked(event)
        # For some reason SQLAlchemy uses old data for the children
        # relationships even when querying the entries again below.
        # Expire them explicitly to avoid having to reload the page
        # after missing menu items have been created.
        for entry in entries:
            db.session.expire(entry, ('children',))
        return MenuEntry.get_for_event(event)
    else:
        # menu is assumed up to date
        return entries


def _build_transient_menu(event):
    """Build the transient event menu from the signal data.

    This is used to check for missing items if customization is
    enabled or for the actual menu if no customization is used
    """
    top_data, child_data = _get_split_signal_entries()
    pos_gen = count()
    return [_build_menu_entry(event, False, data, next(pos_gen), children=child_data.get(data.name))
            for name, data in top_data.items()
            if data.parent is None]


@memoize_request
def menu_entries_for_event(event):
    custom_menu_enabled = layout_settings.get(event, 'use_custom_menu')
    return _build_menu(event) if custom_menu_enabled else _build_transient_menu(event)


def _build_menu_entry(event, custom_menu_enabled, data, position, children=None, parent_id=None):
    entry_cls = MenuEntry if custom_menu_enabled else TransientMenuEntry
    entry = entry_cls(
        event=event,
        is_enabled=data.is_enabled,
        name=data.name,
        position=position,
        new_tab=data.new_tab,
        children=[_build_menu_entry(event, custom_menu_enabled, entry_data, i)
                  for i, entry_data in enumerate(sorted(children or [], key=_menu_entry_key))]
    )

    if parent_id is not None:
        # only valid for non-transient menu entries
        entry.parent_id = parent_id
    if data.plugin:
        entry.type = MenuEntryType.plugin_link
        entry.plugin = data.plugin.name
    else:
        entry.type = MenuEntryType.internal_link
    return entry


@memoize_request
def get_menu_entry_by_name(name, event):
    entries = menu_entries_for_event(event)
    return next((e for e in chain(entries, *(e.children for e in entries)) if e.name == name), None)


def is_menu_entry_enabled(entry_name, event):
    """Check whether the MenuEntry is enabled."""
    return get_menu_entry_by_name(entry_name, event).is_enabled


@dataclass(frozen=True)
class ConferenceTheme:
    """
    Holds the values of a given conference theme to be used by Indico.

    Required:
    - ``name``     -- string indicating the internal name used for the stylesheet which will be
                      stored when the theme is selected in an event.
    - ``css_path`` -- string indicating the relative location of the CSS file
    - ``title``    -- string indicating the title displayed to the user when selecting the theme.

    Optional:
    - ``js_path``  -- string indicating the relative location for a simple, static javascript file
    """

    name: str
    css_path: str
    title: str
    js_path: str = None


def get_plugin_conference_themes():
    data = values_from_signal(signals.plugin.get_conference_themes.send(), return_plugins=True)
    # backwards compatibility in case theme_info is a tuple instead of a `ConferenceTheme``
    data = [(plugin, (theme_info if isinstance(theme_info, ConferenceTheme) else ConferenceTheme(*theme_info)))
            for plugin, theme_info in data]
    return {f'{plugin.name}:{theme_info.name}': theme_info for plugin, theme_info in data}


def _build_css_url(theme):
    if ':' in theme:
        try:
            path = get_plugin_conference_themes()[theme].css_path
        except KeyError:
            return None
        plugin = theme.split(':', 1)[0]
        return url_for_plugin(f'{plugin}.static', filename=path)
    else:
        css_base = url_parse(config.CONFERENCE_CSS_TEMPLATES_BASE_URL).path
        return f'{css_base}/{theme}'


def get_css_url(event, force_theme=None, for_preview=False):
    """Build the URL of a CSS resource.

    :param event: The `Event` to get the CSS url for
    :param force_theme: The ID of the theme to override the custom CSS resource
                        only if it exists
    :param for_preview: Whether the URL is used in the CSS preview page
    :return: The URL to the CSS resource
    """
    from indico.modules.events.layout import layout_settings

    if force_theme and force_theme != '_custom':
        return _build_css_url(force_theme)
    elif for_preview and force_theme is None:
        return None
    elif force_theme == '_custom' or layout_settings.get(event, 'use_custom_css'):
        if not event.has_stylesheet:
            return None
        return url_for('event_layout.css_display', event, slug=event.stylesheet_metadata['hash'])
    elif layout_settings.get(event, 'theme'):
        return _build_css_url(layout_settings.get(event, 'theme'))


def _build_js_url(theme):
    if ':' not in theme:
        return None
    try:
        if not (path := get_plugin_conference_themes()[theme].js_path):
            return None
    except KeyError:
        return None
    plugin = theme.split(':', 1)[0]
    return url_for_plugin(f'{plugin}.static', filename=path)


def get_js_url(event, force_theme=None, for_preview=False):
    """Build the URL of a JS resource.

    :param event: The `Event` to get the JS url for
    :param force_theme: The ID of the theme to import the custom JS resource
                        only if it exists
    :param for_preview: Whether the URL is used in the JS preview page
    :return: The URL to the JS resource
    """
    from indico.modules.events.layout import layout_settings

    if force_theme and force_theme != '_custom':
        return _build_js_url(force_theme)
    elif for_preview and force_theme is None:
        return None
    elif force_theme == '_custom' or layout_settings.get(event, 'use_custom_css'):
        return None
    elif layout_settings.get(event, 'theme'):
        return _build_js_url(layout_settings.get(event, 'theme'))


def get_logo_data(event):
    return {
        'url': event.logo_url,
        'filename': event.logo_metadata['filename'],
        'size': event.logo_metadata['size'],
        'content_type': event.logo_metadata['content_type']
    }


def get_css_file_data(event):
    return {
        'filename': event.stylesheet_metadata['filename'],
        'size': event.stylesheet_metadata['size'],
        'content_type': 'text/css'
    }
