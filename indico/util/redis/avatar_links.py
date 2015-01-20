# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
from MaKaC.common.timezoneUtils import datetimeToUnixTimeInt
from indico.util.redis import scripts
from indico.util.redis import client as redis_client
from indico.util.redis import write_client as redis_write_client


def add_link(avatar, event, role, client=None):
    if client is None:
        client = redis_write_client
    scripts.avatar_event_links_add_link(avatar.getId(), event.getId(), event.getUnixStartDate(), role, client=client)


def del_link(avatar, event, role, client=None):
    if client is None:
        client = redis_write_client
    scripts.avatar_event_links_del_link(avatar.getId(), event.getId(), role, client=client)


def get_links(avatar, minDT=None, maxDT=None, client=None):
    if client is None:
        client = redis_client
    minTS = minDT if isinstance(minDT, int) else datetimeToUnixTimeInt(minDT) if minDT else ''
    maxTS = maxDT if isinstance(maxDT, int) else datetimeToUnixTimeInt(maxDT) if maxDT else ''
    res = scripts.avatar_event_links_get_links(avatar.getId(), minTS, maxTS, client=client)
    if res is None:
        # Execution failed
        return OrderedDict()
    return OrderedDict((eid, set(roles)) for eid, roles in res.iteritems())


def merge_avatars(destination, source, client=None):
    if client is None:
        client = redis_write_client
    scripts.avatar_event_links_merge_avatars(destination.getId(), source.getId(), client=client)


def delete_avatar(avatar, client=None):
    if client is None:
        client = redis_write_client
    scripts.avatar_event_links_delete_avatar(avatar.getId(), client=client)


def update_event_time(event, client=None):
    if client is None:
        client = redis_write_client
    scripts.avatar_event_links_update_event_time(event.getId(), event.getUnixStartDate(), client=client)


def delete_event(event, client=None):
    if client is None:
        client = redis_write_client
    scripts.avatar_event_links_delete_event(event.getId(), client=client)


def init_links(avatar, client=None, assumeEvents=False):
    """Initializes the links based on the existing linked_to data."""

    if client is None:
        client = redis_write_client

    all_events = set()
    event_roles = defaultdict(set)
    for key, roleDict in avatar.linkedTo.iteritems():
        for role, items in roleDict.iteritems():
            for item in items:
                event = event_from_obj(item) if not assumeEvents else item
                if event:
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


def event_from_obj(obj):
    event = None
    if isinstance(obj, MaKaC.conference.Conference):
        event = obj
    elif hasattr(obj, 'getConference'):
        event = obj.getConference()
    if event and event.getId() != 'default':
        return event
