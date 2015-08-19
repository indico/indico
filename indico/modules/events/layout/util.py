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

import binascii
from collections import defaultdict
from itertools import count

import MaKaC
from indico.core import signals
from indico.core.db import db
from indico.modules.events.layout.models.menu import MenuEntry, MenuEntryType
from indico.util.caching import memoize_request
from indico.util.signals import named_objects_from_signal
from indico.modules.events.layout.models.images import ImageFile
from MaKaC.common.cache import GenericCache

_cache = GenericCache('updated-menus')


def _entry_key(entry_data):
    return entry_data.position, entry_data.name


@memoize_request
def get_menu_entries_from_signal():
    return named_objects_from_signal(signals.event.sidemenu.send())


class MenuEntryData(object):
    plugin = None

    def __init__(self, title, name, endpoint, position=0, is_enabled=True, visible=None, parent=None):
        self.title = title
        self.name = name
        self.endpoint = endpoint
        self.position = position
        self._visible = visible
        self.is_enabled = is_enabled
        self.parent = parent

    def visible(self, event):
        return self._visible(event) if self._visible else True


def menu_entries_for_event(event, show_hidden=False):
    from indico.core.plugins import plugin_engine

    entries = MenuEntry.get_for_event(event)
    signal_entries = get_menu_entries_from_signal()

    cache_key = unicode(event.id)
    plugin_hash = binascii.crc32(','.join(sorted(plugin_engine.get_active_plugins()))) & 0xffffffff
    cache_version = '{}:{}'.format(MaKaC.__version__, plugin_hash)
    processed = _cache.get(cache_key) == cache_version

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
        new_entries = [_build_entry(event, data, next(pos_gen), children=children.get(data.name))
                       for (name, data) in sorted(signal_entries.iteritems(), key=lambda (name, data):_entry_key(data))
                       if name in new_entry_names and data.parent is None]

        with db.tmp_session() as sess:
            sess.add_all(new_entries)
            sess.commit()
            _cache.set(cache_key, cache_version)
        entries = MenuEntry.get_for_event(event)

    return entries


def _build_entry(event, data, position, children=None):
    entry = MenuEntry(
        event_id=event.getId(),
        is_enabled=data.is_enabled,
        title=data.title,
        name=data.name,
        position=position,
        children=[_build_entry(event, entry_data, i)
                  for i, entry_data in enumerate(sorted(children or [], key=_entry_key))]
    )

    if data.plugin:
        entry.type = MenuEntryType.plugin_link
        entry.plugin = data.plugin
    else:
        entry.type = MenuEntryType.internal_link
    return entry


def move_entry(entry, to):
    from_ = entry.position
    new_pos = to
    value = -1
    if to is None or to < 0:
        new_pos = to = -1

    if from_ > to:
        new_pos += 1
        from_, to = to, from_
        to -= 1
        value = 1

    entries = MenuEntry.find(MenuEntry.parent_id == entry.parent_id,
                             MenuEntry.event_id == entry.event_id,
                             MenuEntry.position.between(from_ + 1, to))
    for e in entries:
        e.position += value
    entry.position = new_pos


@memoize_request
def get_entry_from_name(name, event):
    return MenuEntry.find_first(
        MenuEntry.name == name,
        MenuEntry.event_id == event.id,
        MenuEntry.type.in_((MenuEntryType.internal_link, MenuEntryType.plugin_link)))


def get_event_logo(event):
    """Retrieves information on the event's logo, or ``None``
       if there is none.
    """
    event = event.as_event
    if event.logo_metadata:
        return {
            'content': event.logo,
            'metadata': event.logo_metadata
        }


def get_images_for_event(event):
    """Return all non-deleted images uploaded to a specific event
    """
    return ImageFile.find_all(event_id=event.id)
