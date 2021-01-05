# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import division, print_function, unicode_literals

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import joinedload, load_only

from indico.modules.events import Event
from indico.modules.events.abstracts.util import get_events_with_abstract_persons
from indico.modules.events.contributions.util import get_events_with_linked_contributions
from indico.modules.events.registration.util import get_events_registered
from indico.modules.events.surveys.util import get_events_with_submitted_surveys
from indico.util.date_time import now_utc, utc_to_server
from indico.util.struct.iterables import window


def _get_blocks(events, attended):
    blocks = []
    block = []
    for event in events:
        if event not in attended:
            if block:
                blocks.append(block)
            block = []
            continue
        block.append(event)
    if block:
        blocks.append(block)
    return blocks


def _query_categ_events(categ, start_dt, end_dt):
    return (Event.query
            .with_parent(categ)
            .filter(Event.happens_between(start_dt, end_dt))
            .options(load_only('id', 'start_dt', 'end_dt')))


def _get_category_score(user, categ, attended_events, debug=False):
    if debug:
        print(repr(categ))
    # We care about events in the whole timespan where the user attended some events.
    # However, this might result in some missed events e.g. if the user was not working for
    # a year and then returned. So we throw away old blocks (or rather adjust the start time
    # to the start time of the newest block)
    first_event_date = attended_events[0].start_dt.replace(hour=0, minute=0)
    last_event_date = attended_events[-1].start_dt.replace(hour=0, minute=0) + timedelta(days=1)
    blocks = _get_blocks(_query_categ_events(categ, first_event_date, last_event_date), attended_events)
    for a, b in window(blocks):
        # More than 3 months between blocks? Ignore the old block!
        if b[0].start_dt - a[-1].start_dt > timedelta(weeks=12):
            first_event_date = b[0].start_dt.replace(hour=0, minute=0)

    # Favorite categories get a higher base score
    score = int(categ in user.favorite_categories)
    if debug:
        print('{0:+.3f} - initial'.format(score))
    # Attendance percentage goes to the score directly. If the attendance is high chances are good that the user
    # is either very interested in whatever goes on in the category or it's something he has to attend regularily.
    total = _query_categ_events(categ, first_event_date, last_event_date).count()
    if total:
        attended_block_event_count = sum(1 for e in attended_events if e.start_dt >= first_event_date)
        score += attended_block_event_count / total
    if debug:
        print('{0:+.3f} - attendance'.format(score))
    # If there are lots/few unattended events after the last attended one we also update the score with that
    total_after = _query_categ_events(categ, last_event_date + timedelta(days=1), None).count()
    if total_after < total * 0.05:
        score += 0.25
    elif total_after > total * 0.25:
        score -= 0.5
    if debug:
        print('{0:+.3f} - unattended new events'.format(score))
    # Lower the score based on how long ago the last attended event was if there are no future events
    # We start applying this modifier only if the event has been more than 40 days in the past to avoid
    # it from happening in case of monthly events that are not created early enough.
    days_since_last_event = (date.today() - last_event_date.date()).days
    if days_since_last_event > 40:
        score -= 0.025 * days_since_last_event
    if debug:
        print('{0:+.3f} - days since last event'.format(score))
    # For events in the future however we raise the score
    now_local = utc_to_server(now_utc())
    attending_future = (_query_categ_events(categ, now_local, last_event_date)
                        .filter(Event.id.in_(e.id for e in attended_events))
                        .all())
    if attending_future:
        score += 0.25 * len(attending_future)
        if debug:
            print('{0:+.3f} - future event count'.format(score))
        days_to_future_event = (attending_future[0].start_dt.date() - date.today()).days
        score += max(0.1, -(max(0, days_to_future_event - 2) / 4) ** (1 / 3) + 2.5)
        if debug:
            print('{0:+.3f} - days to next future event'.format(score))
    return score


def get_category_scores(user, debug=False):
    # XXX: check if we can add some more roles such as 'contributor' to assume attendance
    event_ids = set()
    event_ids.update(id_
                     for id_, roles in get_events_with_abstract_persons(user).iteritems()
                     if 'abstract_submitter' in roles)
    event_ids.update(id_
                     for id_, roles in get_events_with_linked_contributions(user).iteritems()
                     if 'contribution_submission' in roles)
    event_ids |= get_events_registered(user)
    event_ids |= get_events_with_submitted_surveys(user)
    if not event_ids:
        return {}
    attended = (Event.query
                .filter(Event.id.in_(event_ids), ~Event.is_deleted)
                .options(joinedload('category'))
                .order_by(Event.start_dt, Event.id)
                .all())
    categ_events = defaultdict(list)
    for event in attended:
        categ_events[event.category].append(event)
    return dict((categ, _get_category_score(user, categ, events, debug))
                for categ, events in categ_events.iteritems())
