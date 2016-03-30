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

from collections import defaultdict
from itertools import count, chain
from sqlalchemy.exc import IntegrityError

from indico.core import signals
from indico.core.config import Config
from indico.core.db import db
from indico.modules.events.layout import layout_settings
from indico.modules.events.layout.models.images import ImageFile
from indico.modules.events.layout.models.menu import MenuEntry, MenuEntryType, TransientMenuEntry
from indico.util.caching import memoize_request
from indico.util.signals import named_objects_from_signal
from indico.util.string import crc32
from indico.web.flask.util import url_for

import MaKaC
from MaKaC.common.cache import GenericCache

_cache = GenericCache('updated-menus')


def _menu_entry_key(entry_data):
    return entry_data.position == -1, entry_data.position, entry_data.name


@memoize_request
def get_menu_entries_from_signal():
    return named_objects_from_signal(signals.event.sidemenu.send(), plugin_attr='plugin')


def build_menu_entry_name(name, plugin=None):
    """ Builds the proper name for a menu entry.

    Given a menu entry's name and optionally a plugin, returns the
    correct name of the menu entry.

    :param name: str -- The name of the menu entry.
    :param plugin: IndicoPlugin or str -- The plugin (or the name of the
        plugin) which created the entry.
    """
    if plugin:
        plugin = getattr(plugin, 'name', plugin)
        return '{}:{}'.format(plugin, name)
    else:
        return name


class MenuEntryData(object):
    """Container to transmit menu entry-related data via signals

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
    """
    plugin = None

    def __init__(self, title, name, endpoint, position=-1, is_enabled=True, visible=None, parent=None,
                 static_site=False):
        self.title = title
        self._name = name
        self.endpoint = endpoint
        self.position = position
        self._visible = visible
        self.is_enabled = is_enabled
        self.parent = parent
        self.static_site = static_site

    @property
    def name(self):
        return build_menu_entry_name(self._name, self.plugin)

    def visible(self, event):
        return self._visible(event) if self._visible else True


@memoize_request
def menu_entries_for_event(event):
    from indico.core.plugins import plugin_engine

    custom_menu_enabled = layout_settings.get(event, 'use_custom_menu')
    entries = MenuEntry.get_for_event(event) if custom_menu_enabled else []
    signal_entries = get_menu_entries_from_signal()

    cache_key = unicode(event.id)
    plugin_hash = crc32(','.join(sorted(plugin_engine.get_active_plugins())))
    cache_version = '{}:{}'.format(MaKaC.__version__, plugin_hash)
    processed = entries and _cache.get(cache_key) == cache_version

    if not processed:
        # menu entries from signal
        pos_gen = count(start=(entries[-1].position + 1) if entries else 0)
        entry_names = {entry.name for entry in entries}

        # Keeping only new entries from the signal
        new_entry_names = signal_entries.viewkeys() - entry_names

        # Mapping children data to their parent
        children = defaultdict(list)
        for name, data in signal_entries.iteritems():
            if name in new_entry_names and data.parent is not None:
                children[data.parent].append(data)

        # Building the entries
        new_entries = [_build_menu_entry(event, custom_menu_enabled, data, next(pos_gen),
                                         children=children.get(data.name))
                       for (name, data) in sorted(signal_entries.iteritems(),
                                                  key=lambda (name, data): _menu_entry_key(data))
                       if name in new_entry_names and data.parent is None]

        if custom_menu_enabled:
            with db.tmp_session() as sess:
                sess.add_all(new_entries)
                try:
                    sess.commit()
                except IntegrityError as e:
                    # If there are two parallel requests trying to insert a new menu
                    # item one of them will fail with an error due to the unique index.
                    # If the IntegrityError involves that index, we assume it's just the
                    # race condition and ignore it.
                    sess.rollback()
                    if 'ix_uq_menu_entries_event_id_name' not in unicode(e.message):
                        raise
                else:
                    _cache.set(cache_key, cache_version)
            entries = MenuEntry.get_for_event(event)
        else:
            entries = new_entries

    return entries


def _build_menu_entry(event, custom_menu_enabled, data, position, children=None):
    entry_cls = MenuEntry if custom_menu_enabled else TransientMenuEntry
    entry = entry_cls(
        event_id=event.getId(),
        is_enabled=data.is_enabled,
        name=data.name,
        position=position,
        children=[_build_menu_entry(event, custom_menu_enabled, entry_data, i)
                  for i, entry_data in enumerate(sorted(children or [], key=_menu_entry_key))]
    )

    if data.plugin:
        entry.type = MenuEntryType.plugin_link
        entry.plugin = data.plugin.name
    else:
        entry.type = MenuEntryType.internal_link
    return entry


@memoize_request
def get_menu_entry_by_name(name, event):
    entries = menu_entries_for_event(event)
    return next(e for e in chain(entries, *(e.children for e in entries)) if e.name == name)


def get_images_for_event(event):
    """Return all non-deleted images uploaded to a specific event
    """
    return ImageFile.find_all(event_id=event.id)


def get_css_url(event, force_theme=None, for_preview=False):
    """Builds the URL of a CSS resource.

    :param event: The `Event` to get the CSS url for
    :param force_theme: The ID of the theme to override the custom CSS resource
                        only if it exists
    :param for_preview: Whether the URL is used in the CSS preview page
    :return: The URL to the CSS resource
    """
    from indico.modules.events.layout import layout_settings

    if force_theme and force_theme != '_custom':
        return "{}/{}".format(Config.getInstance().getCssConfTemplateBaseURL(), force_theme)
    elif for_preview and force_theme is None:
        return None
    elif force_theme == '_custom' or layout_settings.get(event, 'use_custom_css'):
        if not event.has_stylesheet:
            return None
        return url_for('event_layout.css_display', event, slug=event.stylesheet_metadata['hash'])
    elif layout_settings.get(event, 'theme'):
        return "{}/{}".format(Config.getInstance().getCssConfTemplateBaseURL(), layout_settings.get(event, 'theme'))


def is_menu_entry_enabled(entry_name, event):
    """Check whether the MenuEntry is enabled"""
    return get_menu_entry_by_name(entry_name, event).is_enabled
