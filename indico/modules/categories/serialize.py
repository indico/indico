# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO

from feedgen.feed import FeedGenerator
from flask import session
from sqlalchemy.orm import joinedload, load_only, subqueryload, undefer

from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.events.ical import events_to_ical
from indico.util.string import sanitize_html


def serialize_categories_ical(category_ids, user, event_filter=True, event_filter_fn=None, update_query=None):
    """Export the events in a category to iCal.

    :param category_ids: Category IDs to export
    :param user: The user who needs to be able to access the events
    :param event_filter: A SQLalchemy criterion to restrict which
                         events will be returned.  Usually something
                         involving the start/end date of the event.
    :param event_filter_fn: A callable that determines which events to include (after querying)
    :param update_query: A callable that can update the query used to retrieve the events.
                         Must return the updated query object.
    """
    own_room_strategy = joinedload('own_room')
    own_room_strategy.load_only('building', 'floor', 'number', 'verbose_name')
    own_room_strategy.lazyload('owner')
    own_venue_strategy = joinedload('own_venue').load_only('name')
    query = (Event.query
             .filter(Event.category_chain_overlaps(category_ids),
                     ~Event.is_deleted,
                     event_filter)
             .options(load_only('id', 'category_id', 'start_dt', 'end_dt', 'title', 'description', 'own_venue_name',
                                'own_room_name', 'protection_mode', 'access_key'),
                      subqueryload('acl_entries'),
                      joinedload('person_links'),
                      own_room_strategy,
                      own_venue_strategy)
             .order_by(Event.start_dt))
    if update_query:
        query = update_query(query)
    it = iter(query)
    if event_filter_fn:
        it = filter(event_filter_fn, it)
    events = list(it)
    # make sure the parent categories are in sqlalchemy's identity cache.
    # this avoids query spam from `protection_parent` lookups
    _parent_categs = (Category._get_chain_query(Category.id.in_({e.category_id for e in events}))  # noqa: F841,RUF100
                      .options(load_only('id', 'parent_id', 'protection_mode'),
                               joinedload('acl_entries'))
                      .all())

    return BytesIO(events_to_ical(events, user))


def serialize_category_atom(category, url, user, event_filter):
    """Export the events in a category to Atom.

    :param category: The category to export
    :param url: The URL of the feed
    :param user: The user who needs to be able to access the events
    :param event_filter: A SQLalchemy criterion to restrict which
                         events will be returned.  Usually something
                         involving the start/end date of the event.
    """
    query = (Event.query
             .filter(Event.category_chain_overlaps(category.id),
                     Event.is_visible_in(category.id),
                     ~Event.is_deleted,
                     event_filter)
             .options(load_only('id', 'category_id', 'start_dt', 'title', 'description', 'protection_mode',
                                'access_key'),
                      subqueryload('acl_entries'))
             .order_by(Event.start_dt))
    events = [e for e in query if e.can_access(user)]

    feed = FeedGenerator()
    feed.id(url)
    feed.title(f'Indico Feed [{category.title}]')
    feed.link(href=url, rel='self')

    for event in events:
        entry = feed.add_entry(order='append')
        entry.id(event.external_url)
        entry.title(event.title)
        entry.summary(sanitize_html(str(event.description)) or None, type='html')
        entry.link(href=event.external_url)
        entry.updated(event.start_dt)
    return BytesIO(feed.atom_str(pretty=True))


def serialize_category(category, with_favorite=False, with_path=False, parent_path=None, child_path=None):
    data = {
        'id': category.id,
        'title': category.title,
        'is_protected': category.is_protected,
        'has_events': category.has_events,
        'has_children': category.has_children,
        'deep_category_count': category.deep_children_count,
        'deep_event_count': category.deep_events_count,
        'can_access': category.can_access(session.user),
        'can_create_events': category.can_create_events(session.user),
        'can_propose_events': category.can_propose_events(session.user),
        'can_manage': category.can_manage(session.user),
    }
    if with_path:
        if child_path:
            data['path'] = child_path[:]
            for __ in reversed(child_path):
                data['path'].pop()
                if not data['path'] or data['path'][-1]['id'] == category.id:
                    break
        elif parent_path:
            data['path'] = parent_path[:]
            data['path'].append({'id': category.id, 'title': category.title})
        else:
            data['path'] = category.chain
        data['parent_path'] = data['path'][:-1]
    if with_favorite:
        data['is_favorite'] = session.user and category in session.user.favorite_categories
    return data


def serialize_category_chain(category, include_children=False, include_parents=False):
    data = {'category': serialize_category(category, with_path=True)}
    if include_children:
        data['subcategories'] = [serialize_category(c, with_path=True, parent_path=data['category']['path'])
                                 for c in category.children]
    if include_parents:
        query = (category.parent_chain_query
                 .options(undefer('deep_events_count'), undefer('deep_children_count')))
        data['supercategories'] = [serialize_category(c, with_path=True, child_path=data['category']['path'])
                                   for c in query]
    return data
