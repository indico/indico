# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
from operator import attrgetter

from flask import render_template, session
from pytz import utc
from sqlalchemy import Date, cast
from sqlalchemy.orm import contains_eager, joinedload, subqueryload, undefer

from indico.core.db import db
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.models.events import Event
from indico.modules.events.models.persons import EventPersonLink
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable.legacy import TimetableSerializer, serialize_event_info
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.util.caching import memoize_request
from indico.util.date_time import format_time, get_day_end, iterdays
from indico.util.i18n import _
from indico.util.string import to_unicode
from indico.web.flask.templating import get_template_module
from indico.web.forms.colors import get_colors


def _query_events(categ_ids, day_start, day_end):
    event = db.aliased(Event)
    dates_overlap = lambda t: (t.start_dt >= day_start) & (t.start_dt <= day_end)
    return (db.session.query(Event.id, TimetableEntry.start_dt)
            .filter(
                Event.category_chain_overlaps(categ_ids),
                ~Event.is_deleted,
                ((Event.timetable_entries.any(dates_overlap(TimetableEntry))) |
                 (Event.query.exists().where(
                     Event.happens_between(day_start, day_end) &
                     (Event.id == event.id)))))
            .group_by(Event.id, TimetableEntry.start_dt)
            .order_by(Event.id, TimetableEntry.start_dt)
            .join(TimetableEntry,
                  (TimetableEntry.event_id == Event.id) & (dates_overlap(TimetableEntry)),
                  isouter=True))


def _query_blocks(event_ids, dates_overlap, detail_level='session'):
    options = [subqueryload('session').joinedload('blocks').joinedload('person_links')]

    if detail_level == 'contribution':
        options.append(contains_eager(SessionBlock.timetable_entry).joinedload(TimetableEntry.children))
    else:
        options.append(contains_eager(SessionBlock.timetable_entry))

    return (SessionBlock.find(~Session.is_deleted,
                              Session.event_id.in_(event_ids),
                              dates_overlap(TimetableEntry))
            .options(*options)
            .join(TimetableEntry)
            .join(Session))


def find_latest_entry_end_dt(obj, day=None):
    """Get the latest end datetime for timetable entries within the object.

    :param obj: The :class:`Event` or :class:`SessionBlock` that will be used to
                look for timetable entries.
    :param day: The local event date to look for timetable entries.  Applicable only
                to ``Event``.
    :return: The end datetime of the timetable entry finishing the latest. ``None``
              if no entry was found.
    """
    if isinstance(obj, Event):
        if day is None:
            raise ValueError("No day specified for event.")
        if not (obj.start_dt_local.date() <= day <= obj.end_dt_local.date()):
            raise ValueError("Day out of event bounds.")
        entries = obj.timetable_entries.filter(TimetableEntry.parent_id.is_(None),
                                               cast(TimetableEntry.start_dt.astimezone(obj.tzinfo), Date) == day).all()
    elif isinstance(obj, SessionBlock):
        if day is not None:
            raise ValueError("Day specified for session block.")
        entries = obj.timetable_entry.children
    else:
        raise ValueError("Invalid object type {}".format(type(obj)))
    return max(entries, key=attrgetter('end_dt')).end_dt if entries else None


def find_next_start_dt(duration, obj, day=None, force=False):
    """Find the next most convenient start date fitting a duration within an object.

    :param duration: Duration to fit into the event/session-block.
    :param obj: The :class:`Event` or :class:`SessionBlock` the duration needs to
                fit into.
    :param day: The local event date where to fit the duration in case the object is
                an event.
    :param force: Gives earliest datetime if the duration doesn't fit.
    :return: The end datetime of the latest scheduled entry in the object if the
              duration fits then. It it doesn't, the latest datetime that fits it.
              ``None`` if the duration cannot fit in the object, earliest datetime
              if ``force`` is ``True``.
    """
    if isinstance(obj, Event):
        if day is None:
            raise ValueError("No day specified for event.")
        if not (obj.start_dt_local.date() <= day <= obj.end_dt_local.date()):
            raise ValueError("Day out of event bounds.")
        earliest_dt = obj.start_dt if obj.start_dt_local.date() == day else obj.start_dt.replace(hour=8, minute=0)
        latest_dt = obj.end_dt if obj.start_dt.date() == day else get_day_end(day, tzinfo=obj.tzinfo)
    elif isinstance(obj, SessionBlock):
        if day is not None:
            raise ValueError("Day specified for session block.")
        earliest_dt = obj.timetable_entry.start_dt
        latest_dt = obj.timetable_entry.end_dt
    else:
        raise ValueError("Invalid object type {}".format(type(obj)))
    max_duration = latest_dt - earliest_dt
    if duration > max_duration:
        return earliest_dt if force else None
    start_dt = find_latest_entry_end_dt(obj, day=day) or earliest_dt
    end_dt = start_dt + duration
    if end_dt > latest_dt:
        start_dt = latest_dt - duration
    return start_dt


def get_category_timetable(categ_ids, start_dt, end_dt, detail_level='event', tz=utc, from_categ=None, grouped=True):
    """Retrieve time blocks that fall within a specific time interval
       for a given set of categories.

       :param categ_ids: iterable containing list of category IDs
       :param start_dt: start of search interval (``datetime``, expected
                        to be in display timezone)
       :param end_dt: end of search interval (``datetime`` in expected
                      to be in display timezone)
       :param detail_level: the level of detail of information
                            (``event|session|contribution``)
       :param tz: the ``timezone`` information should be displayed in
       :param from_categ: ``Category`` that will be taken into account to calculate
                          visibility
       :param grouped: Whether to group results by start date
       :returns: a dictionary containing timetable information in a
                 structured way. See source code for examples.
    """
    day_start = start_dt.astimezone(utc)
    day_end = end_dt.astimezone(utc)
    dates_overlap = lambda t: (t.start_dt >= day_start) & (t.start_dt <= day_end)

    items = defaultdict(lambda: defaultdict(list))

    # first of all, query TimetableEntries/events that fall within
    # specified range of dates (and category set)
    events = _query_events(categ_ids, day_start, day_end)
    if from_categ:
        events = events.filter(Event.is_visible_in(from_categ))
    for eid, tt_start_dt in events:
        if tt_start_dt:
            items[eid][tt_start_dt.astimezone(tz).date()].append(tt_start_dt)
        else:
            items[eid] = None

    # then, retrieve detailed information about the events
    event_ids = set(items)
    query = (Event.find(Event.id.in_(event_ids))
             .options(subqueryload(Event.person_links).joinedload(EventPersonLink.person),
                      joinedload(Event.own_room).noload('owner'),
                      joinedload(Event.own_venue),
                      joinedload(Event.category).undefer('effective_icon_data'),
                      undefer('effective_protection_mode')))
    scheduled_events = defaultdict(list)
    ongoing_events = []
    events = []
    for e in query:
        if grouped:
            local_start_dt = e.start_dt.astimezone(tz).date()
            local_end_dt = e.end_dt.astimezone(tz).date()
            if items[e.id] is None:
                # if there is no TimetableEntry, this means the event has not timetable on that interval
                for day in iterdays(max(start_dt.date(), local_start_dt), min(end_dt.date(), local_end_dt)):
                    # if the event starts on this date, we've got a time slot
                    if day.date() == local_start_dt:
                        scheduled_events[day.date()].append((e.start_dt, e))
                    else:
                        ongoing_events.append(e)
            else:
                for start_d, start_dts in items[e.id].viewitems():
                    scheduled_events[start_d].append((start_dts[0], e))
        else:
            events.append(e)

    # result['events'][date(...)] -> [(datetime(....), Event(...))]
    # result[event_id]['contribs'][date(...)] -> [(TimetableEntry(...), Contribution(...))]
    # result['ongoing_events'] = [Event(...)]
    if grouped:
        result = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    else:
        result = defaultdict(lambda: defaultdict(list))

    result.update({
        'events': scheduled_events if grouped else events,
        'ongoing_events': ongoing_events
    })

    # according to detail level, ask for extra information from the DB
    if detail_level != 'event':
        query = _query_blocks(event_ids, dates_overlap, detail_level)
        if grouped:
            for b in query:
                start_date = b.timetable_entry.start_dt.astimezone(tz).date()
                result[b.session.event_id]['blocks'][start_date].append((b.timetable_entry, b))
        else:
            for b in query:
                result[b.session.event_id]['blocks'].append(b)

    if detail_level == 'contribution':
        query = (Contribution.find(Contribution.event_id.in_(event_ids),
                                   dates_overlap(TimetableEntry),
                                   ~Contribution.is_deleted)
                 .options(contains_eager(Contribution.timetable_entry),
                          joinedload(Contribution.person_links))
                 .join(TimetableEntry))
        if grouped:
            for c in query:
                start_date = c.timetable_entry.start_dt.astimezone(tz).date()
                result[c.event_id]['contribs'][start_date].append((c.timetable_entry, c))
        else:
            for c in query:
                result[c.event_id]['contributions'].append(c)

        query = (Break.find(TimetableEntry.event_id.in_(event_ids), dates_overlap(TimetableEntry))
                 .options(contains_eager(Break.timetable_entry))
                 .join(TimetableEntry))
        if grouped:
            for b in query:
                start_date = b.timetable_entry.start_dt.astimezone(tz).date()
                result[b.timetable_entry.event_id]['breaks'][start_date].append((b.timetable_entry, b))
        else:
            for b in query:
                result[b.timetable_entry.event_id]['breaks'].append(b)
    return result


def render_entry_info_balloon(entry, editable=False, sess=None):
    if entry.break_:
        return render_template('events/timetable/balloons/break.html', break_=entry.break_, editable=editable,
                               can_manage_event=entry.event.can_manage(session.user), color_list=get_colors(),
                               event_locked=entry.event.is_locked)
    elif entry.contribution:
        return render_template('events/timetable/balloons/contribution.html', contrib=entry.contribution,
                               editable=editable,
                               can_manage_event=entry.event.can_manage(session.user),
                               can_manage_contributions=sess.can_manage_contributions(session.user) if sess else True,
                               event_locked=entry.event.is_locked)
    elif entry.session_block:
        return render_template('events/timetable/balloons/block.html', block=entry.session_block, editable=editable,
                               can_manage_session=sess.can_manage(session.user) if sess else True,
                               can_manage_blocks=sess.can_manage_blocks(session.user) if sess else True,
                               color_list=get_colors(), event_locked=entry.event.is_locked)
    else:
        raise ValueError("Invalid entry")


def render_session_timetable(session, timetable_layout=None, management=False):
    if not session.start_dt:
        # no scheduled sessions present
        return ''
    timetable_data = TimetableSerializer(session.event).serialize_session_timetable(session, without_blocks=True,
                                                                                    strip_empty_days=True)
    event_info = serialize_event_info(session.event)
    tpl = get_template_module('events/timetable/_timetable.html')
    return tpl.render_timetable(timetable_data, event_info, timetable_layout=timetable_layout, management=management)


def get_session_block_entries(event, day):
    """Returns a list of event top-level session blocks for the given `day`"""
    return (event.timetable_entries
            .filter(db.cast(TimetableEntry.start_dt.astimezone(event.tzinfo), db.Date) == day.date(),
                    TimetableEntry.type == TimetableEntryType.SESSION_BLOCK)
            .all())


def shift_following_entries(entry, shift, session_=None):
    """Reschedules entries starting after the given entry by the given shift."""
    query = entry.siblings_query.filter(TimetableEntry.start_dt >= entry.end_dt)
    if session_ and not entry.parent:
        query.filter(TimetableEntry.type == TimetableEntryType.SESSION_BLOCK,
                     TimetableEntry.session_block.has(session_id=session_.id))
    entries = query.all()
    if not entries:
        return []
    for sibling in entries:
        sibling.move(sibling.start_dt + shift)


def get_timetable_offline_pdf_generator(event):
    from indico.legacy.pdfinterface.conference import TimeTablePlain, TimetablePDFFormat
    pdf_format = TimetablePDFFormat()
    return TimeTablePlain(event, session.user, sortingCrit=None, ttPDFFormat=pdf_format, pagesize='A4',
                          fontsize='normal')


def get_time_changes_notifications(changes, tzinfo, entry=None):
    notifications = []
    for obj, change in changes.iteritems():
        if entry:
            if entry.object == obj:
                continue
            if not isinstance(obj, Event) and obj.timetable_entry in entry.children:
                continue
        msg = None
        if isinstance(obj, Event):
            if 'start_dt' in change:
                new_time = change['start_dt'][1]
                msg = _("Event start time changed to {}")
            elif 'end_dt' in change:
                new_time = change['end_dt'][1]
                msg = _("Event end time changed to {}")
            else:
                raise ValueError("Invalid change in event.")
        elif isinstance(obj, SessionBlock):
            if 'start_dt' in change:
                new_time = change['start_dt'][1]
                msg = _("Session block start time changed to {}")
            elif 'end_dt' in change:
                new_time = change['end_dt'][1]
                msg = _("Session block end time changed to {}")
            else:
                raise ValueError("Invalid change in session block.")
        if msg:
            notifications.append(msg.format(to_unicode(format_time(new_time, timezone=tzinfo))))
    return notifications


@memoize_request
def get_top_level_entries(event):
    return event.timetable_entries.filter_by(parent_id=None).all()


@memoize_request
def get_nested_entries(event):
    entries = event.timetable_entries.filter(TimetableEntry.parent_id.isnot(None)).all()
    result = defaultdict(list)
    for entry in entries:
        result[entry.parent_id].append(entry)
    return result
