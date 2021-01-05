# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.orm import contains_eager

from indico.core.plugins import plugin_engine
from indico.modules.events import Event
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.util.i18n import _


def get_vc_plugins():
    """Return a dict containing the available videoconference plugins."""
    from indico.modules.vc import VCPluginMixin
    return {p.service_name: p for p in plugin_engine.get_active_plugins().itervalues() if isinstance(p, VCPluginMixin)}


def resolve_title(obj):
    return obj.full_title if isinstance(obj, SessionBlock) else obj.title


def get_linked_to_description(obj):
    return {
        'event': _('{} (event)'),
        'contribution': _('{} (contribution)'),
        'block': _('{} (session block)'),
    }[obj.link_type.name].format(resolve_title(obj.link_object))


def get_managed_vc_plugins(user):
    """Return the plugins the user can manage."""
    return [p for p in get_vc_plugins().itervalues() if p.can_manage_vc(user)]


def find_event_vc_rooms(from_dt=None, to_dt=None, distinct=False):
    """Find VC rooms matching certain criteria.

    :param from_dt: earliest event/contribution to include
    :param to_dt: latest event/contribution to include
    :param distinct: if True, never return the same ``(event, vcroom)``
                     more than once (even if it's linked more than once to
                     that event)
    """
    from indico.modules.vc.models.vc_rooms import VCRoomEventAssociation
    event_strategy = contains_eager('event')
    event_strategy.joinedload('own_room').noload('owner')
    event_strategy.joinedload('own_venue')
    query = (VCRoomEventAssociation.query
             .join(VCRoomEventAssociation.event)
             .options(event_strategy))
    if distinct:
        query = query.distinct(VCRoomEventAssociation.event_id, VCRoomEventAssociation.vc_room_id)
    if from_dt is not None or to_dt is not None:
        if from_dt is not None:
            query = query.filter(Event.start_dt >= from_dt)
        if to_dt is not None:
            query = query.filter(Event.start_dt < to_dt)
    for vc_room in query:
        yield vc_room
