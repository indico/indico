# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, session
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import NotFound

from indico.core.config import config
from indico.modules.events.contributions import Contribution
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable import TimetableEntry
from indico.modules.rb.event.forms import BookingListForm
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence, ReservationOccurrenceLink
from indico.modules.rb.util import get_booking_params_for_event, rb_check_if_visible
from indico.modules.rb.views import WPEventBookingList
from indico.util.date_time import format_datetime, now_utc
from indico.util.i18n import _


def _contrib_query(event):
    return (Contribution.query
            .with_parent(event)
            .filter(Contribution.is_scheduled,
                    Contribution.timetable_entry.has(TimetableEntry.start_dt > now_utc()))
            .options(joinedload('timetable_entry'))
            .order_by(Contribution.friendly_id))


def _session_block_query(event):
    return (SessionBlock.query
            .filter(SessionBlock.session.has(event=event),
                    SessionBlock.timetable_entry.has(TimetableEntry.start_dt > now_utc()))
            .options(joinedload('timetable_entry'))
            .join(Session)
            .order_by(Session.friendly_id, Session.title, SessionBlock.title))


class RHEventBookingList(RHManageEventBase):
    def _check_access(self):
        RHManageEventBase._check_access(self)
        if not config.ENABLE_ROOMBOOKING:
            raise NotFound(_('The room booking module is not enabled.'))

    def _process(self):
        form = BookingListForm(event=self.event)
        has_contribs = _contrib_query(self.event).has_rows()
        has_session_blocks = _session_block_query(self.event).has_rows()

        links = (ReservationOccurrenceLink.query.with_parent(self.event)
                 .options(joinedload('reservation_occurrence').joinedload('reservation').joinedload('room'),
                          joinedload('session_block'),
                          joinedload('contribution'))
                 .filter(~ReservationOccurrenceLink.reservation_occurrence.has(ReservationOccurrence.is_cancelled))
                 .join(ReservationOccurrence)
                 .order_by(ReservationOccurrence.start_dt)
                 .all())

        contribs_data = {c.id: {'start_dt': c.start_dt.isoformat(), 'end_dt': c.end_dt.isoformat()}
                         for c in _contrib_query(self.event)}
        session_blocks_data = {sb.id: {'start_dt': sb.start_dt.isoformat(), 'end_dt': sb.end_dt.isoformat()}
                               for sb in _session_block_query(self.event)}
        is_past_event = self.event.end_dt < now_utc()
        event_rb_params = get_booking_params_for_event(self.event)
        is_rb_visible = rb_check_if_visible(session.user)
        return WPEventBookingList.render_template('booking_list.html', self.event,
                                                  form=form,
                                                  links=links,
                                                  has_contribs=has_contribs,
                                                  contribs_data=contribs_data,
                                                  has_session_blocks=has_session_blocks,
                                                  session_blocks_data=session_blocks_data,
                                                  event_rb_params=event_rb_params,
                                                  is_past_event=is_past_event,
                                                  is_rb_visible=is_rb_visible)


class RHListLinkableContributions(RHManageEventBase):
    """AJAX endpoint that lists all contributions in the event."""

    def _process(self):
        query = _contrib_query(self.event)
        result = [{'id': contrib.id,
                   'friendly_id': contrib.friendly_id,
                   'title': contrib.title,
                   'full_title': contrib.verbose_title}
                  for contrib in query]
        return jsonify(result)


class RHListLinkableSessionBlocks(RHManageEventBase):
    """AJAX endpoint that lists all session blocks in the event."""

    def _process(self):
        query = _session_block_query(self.event)
        result = [{'id': session_block.id,
                   'friendly_id': session_block.session.friendly_id,
                   'title': session_block.full_title,
                   'full_title': '#{}: {} ({})'.format(  # noqa: UP032
                       session_block.session.friendly_id, session_block.full_title,
                       format_datetime(session_block.timetable_entry.start_dt))}
                  for session_block in query]
        return jsonify(result)
