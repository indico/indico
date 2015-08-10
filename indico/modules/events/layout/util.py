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
from itertools import count

from indico.core import signals
from indico.core.db import db
from indico.modules.events.models.events import Event
from indico.modules.events.layout.models.menu import MenuEntry, MenuEntryType
from indico.util.signals import named_objects_from_signal
from MaKaC.common.cache import GenericCache


class MenuEntryData(object):
    plugin = None

    def __init__(self, title, name, endpoint, visible_default=True, visible=None, children=None):
        self.title = title
        self.name = name
        self.endpoint = endpoint
        self._visible = visible
        self.visible_default = visible_default
        self.children = children if children is not None else []

    def visible(self, event):
        return self._visible(event) if self._visible else self.visible_default


_cache = GenericCache('updated-menus')


def menu_entries_for_event(event, show_hidden=False):
    from indico.core.plugins import plugin_engine

    entries = MenuEntry.find(event_id=event.getId(), parent_id=None).order_by(MenuEntry.position).all()
    signal_entries = named_objects_from_signal(signals.event.sidemenu.send())

    plugin_key = ','.join(sorted(plugin_engine.get_active_plugins()))
    cache_key = binascii.crc32('{}_{}'.format(event.getId(), plugin_key)) & 0xffffffff
    processed = _cache.get(cache_key)

    if not processed:
        # menu entries from signal
        pos_gen = count(start=(entries[-1].position + 1) if entries else 0)
        entry_names = {entry.name for entry in entries}

        signal_entry_names = signal_entries.viewkeys()

        # Keeping only new entries from the signal
        new_entry_names = signal_entry_names - entry_names
        new_entries = [_build_entry(event, data, position=position)
                       for (name, data), position in zip(signal_entries.iteritems(), pos_gen)
                       if name in new_entry_names]

        with db.tmp_session() as sess:
            sess.add_all(new_entries)
            sess.commit()
            _cache.set(cache_key, True)
        entries.extend(new_entries)

    def _is_entry_visible(entry):
        if not show_hidden and not entry.visible:
            return False
        if entry.name:
            try:
                entry_data = signal_entries[entry.name]
            except KeyError:
                return False
            if show_hidden:
                return True
            if callable(entry_data.visible):
                return entry_data.visible(event)

    entries = filter(_is_entry_visible, entries)
    return entries


def _build_entry(event, data, position=0):
    entry = MenuEntry(
        event_id=event.getId(),
        visible=data.visible_default,
        title=data.title,
        name=data.name,
        endpoint=data.endpoint,
        position=position,
        children=[_build_entry(event, entry_data, i) for i, entry_data in enumerate(data.children or [])]
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


def get_event_logo(event):
    """Retrieves information on the event's logo, or ``None``
       if there is none.
    """
    event = Event.get(event.id)
    if event.logo_metadata:
        return {
            'content': event.logo,
            'metadata': event.logo_metadata
        }
