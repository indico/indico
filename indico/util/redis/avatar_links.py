# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from collections import defaultdict, OrderedDict
import MaKaC
from indico.util.redis import scripts


def add_link(client, avatar, event, role):
    scripts.avatar_event_links_add_link(avatar.getId(), event.getId(), event.getUnixStartDate(), role, client=client)


def del_link(client, avatar, event, role):
    scripts.avatar_event_links_del_link(avatar.getId(), event.getId(), role, client=client)


def get_links(client, avatar):
    return OrderedDict((eid, set(roles)) for eid, roles in
                       scripts.avatar_event_links_get_links(avatar.getId(), client=client).iteritems())


def merge_avatars(client, destination, source):
    scripts.avatar_event_links_merge_avatars(destination.getId(), source.getId(), client=client)


def delete_avatar(client, avatar):
    scripts.avatar_event_links_delete_avatar(avatar.getId(), client=client)


def update_event_time(client, event):
    scripts.avatar_event_links_update_event_time(event.getId(), event.getUnixStartDate(), client=client)


def delete_event(client, event):
    scripts.avatar_event_links_delete_event(event.getId(), client=client)


def init_links(client, avatar):
    """Initializes the links based on the existing linked_to data."""

    all_events = set()
    event_roles = defaultdict(set)
    for key, roleDict in avatar.linkedTo.iteritems():
        for role, items in roleDict.iteritems():
            for item in items:
                event = None
                if isinstance(item, MaKaC.conference.Conference):
                    event = item
                elif hasattr(item, 'getConference'):
                    event = item.getConference()
                if event is None:
                    continue
                elif event.getId() == 'default':  # DefaultConference
                    continue
                all_events.add(event)
                event_roles[event].add(key + '_' + role)

    # Add avatar to event avatar lists
    for event in all_events:
        client.sadd('avatar-event-links/event_avatars:%s' % event.getId(), avatar.getId())
    # Add events to avatar event list
    zdata = dict((e.getId(), e.getUnixStartDate()) for e in all_events)
    if zdata:
        client.zadd('avatar-event-links/avatar_events:%s' % avatar.getId(), **zdata)
    # Add roles to avatar-event role lists
    for event, roles in event_roles.iteritems():
        client.sadd('avatar-event-links/avatar_event_roles:%s:%s' % (avatar.getId(), event.getId()), *roles)