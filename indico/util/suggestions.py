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

from __future__ import division
from collections import defaultdict
from datetime import date, timedelta
from operator import methodcaller

from MaKaC.common.indexes import IndexesHolder
from MaKaC.common.timezoneUtils import nowutc, utc2server
from MaKaC.conference import ConferenceHolder
from indico.modules.events.surveys.util import get_events_with_submitted_surveys
from indico.util.redis import avatar_links
from indico.util.struct.iterables import window


def _unique(seq, get_identity=None):
    exclude = set()
    for item in seq:
        identifier = get_identity(item) if get_identity else item
        if identifier not in exclude:
            exclude.add(identifier)
            yield item


def _unique_events(seq):
    return _unique(seq, methodcaller('getId'))


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


def _get_category_score(user, categ, attended_events, debug=False):
    # avoid stale SQLAlchemy object
    if debug:
        print repr(categ)
    idx = IndexesHolder().getById('categoryDateAll')
    attended_events_set = set(attended_events)
    # We care about events in the whole timespan where the user attended some events.
    # However, this might result in some missed events e.g. if the user was not working for
    # a year and then returned. So we throw away old blocks (or rather adjust the start time
    # to the start time of the newest block)
    first_event_date = attended_events[0].getStartDate().replace(hour=0, minute=0)
    last_event_date = attended_events[-1].getStartDate().replace(hour=0, minute=0) + timedelta(days=1)
    blocks = _get_blocks(_unique_events(idx.iterateObjectsIn(categ.getId(), first_event_date, last_event_date)),
                         attended_events_set)
    for a, b in window(blocks):
        # More than 3 months between blocks? Ignore the old block!
        if b[0].getStartDate() - a[-1].getStartDate() > timedelta(weeks=12):
            first_event_date = b[0].getStartDate().replace(hour=0, minute=0)

    # Favorite categories get a higher base score
    favorite = categ in user.favorite_categories
    score = 1 if favorite else 0
    if debug:
        print '{0:+.3f} - initial'.format(score)
    # Attendance percentage goes to the score directly. If the attendance is high chances are good that the user
    # is either very interested in whatever goes on in the category or it's something he has to attend regularily.
    total = sum(1 for _ in _unique_events(idx.iterateObjectsIn(categ.getId(), first_event_date, last_event_date)))
    if total:
        attended_block_event_count = sum(1 for e in attended_events_set if e.getStartDate() >= first_event_date)
        score += attended_block_event_count / total
    if debug:
        print '{0:+.3f} - attendance'.format(score)
    # If there are lots/few unattended events after the last attended one we also update the score with that
    total_after = sum(1 for _ in _unique_events(idx.iterateObjectsIn(categ.getId(),
                                                                     last_event_date + timedelta(days=1),
                                                                     None)))
    if total_after < total * 0.05:
        score += 0.25
    elif total_after > total * 0.25:
        score -= 0.5
    if debug:
        print '{0:+.3f} - unattended new events'.format(score)
    # Lower the score based on how long ago the last attended event was if there are no future events
    # We start applying this modifier only if the event has been more than 40 days in the past to avoid
    # it from happening in case of monthly events that are not created early enough.
    days_since_last_event = (date.today() - last_event_date.date()).days
    if days_since_last_event > 40:
        score -= 0.025 * days_since_last_event
    if debug:
        print '{0:+.3f} - days since last event'.format(score)
    # For events in the future however we raise the score
    now_local = utc2server(nowutc(), False)
    attending_future = [e for e in _unique_events(idx.iterateObjectsIn(categ.getId(), now_local, last_event_date))
                        if e in attended_events_set]
    if attending_future:
        score += 0.25 * len(attending_future)
        if debug:
            print '{0:+.3f} - future event count'.format(score)
        days_to_future_event = (attending_future[0].getStartDate().date() - date.today()).days
        score += max(0.1, -(max(0, days_to_future_event - 2) / 4) ** (1 / 3) + 2.5)
        if debug:
            print '{0:+.3f} - days to next future event'.format(score)
    return score


def get_category_scores(user, debug=False):
    attendance_roles = {'contribution_submission', 'abstract_submitter', 'registration_registrant', 'survey_submitter'}
    links = avatar_links.get_links(user)
    for event_id in get_events_with_submitted_surveys(user):
        links.setdefault(str(event_id), set()).add('survey_submitter')
    ch = ConferenceHolder()
    attended = filter(None, (ch.getById(eid, True) for eid, roles in links.iteritems() if attendance_roles & roles))
    categ_events = defaultdict(list)
    for event in attended:
        categ_events[event.getOwner()].append(event)
    return dict((categ, _get_category_score(user, categ, events, debug))
                for categ, events in categ_events.iteritems())
