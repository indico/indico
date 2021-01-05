# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import redirect, session
from werkzeug.exceptions import Forbidden

from indico.core import signals
from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.management.forms import (EventClassificationForm, EventContactInfoForm, EventDataForm,
                                                    EventDatesForm, EventLocationForm, EventPersonsForm)
from indico.modules.events.management.util import flash_if_unregistered
from indico.modules.events.management.views import WPEventSettings, render_event_management_header_right
from indico.modules.events.models.events import EventType
from indico.modules.events.models.labels import EventLabel
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.operations import update_event
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.modules.events.util import track_time_changes
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
from indico.util.signals import values_from_signal
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHEventSettings(RHManageEventBase):
    """Event settings dashboard."""

    def _check_access(self):
        if not session.user:
            raise Forbidden
        # If the user cannot manage the whole event see if anything gives them
        # limited management access.
        if not self.event.can_manage(session.user):
            urls = sorted(values_from_signal(signals.event_management.management_url.send(self.event),
                                             single_value=True))
            response = redirect(urls[0]) if urls else None
            raise Forbidden(response=response)

        RHManageEventBase._check_access(self)  # mainly to trigger the legacy "event locked" check

    def _process(self):
        from indico.modules.events.contributions import contribution_settings

        show_booking_warning = False
        if (config.ENABLE_ROOMBOOKING and not self.event.has_ended and self.event.room
                and not self.event.room_reservation_links):
            # Check if any of the managers of the event already have a booking that overlaps with the event datetime
            manager_ids = [p.user.id for p in self.event.acl_entries if p.user]
            has_overlap = (ReservationOccurrence.query
                           .filter(ReservationOccurrence.is_valid,
                                   db.or_(Reservation.booked_for_id.in_(manager_ids),
                                          Reservation.created_by_id.in_(manager_ids)),
                                   db_dates_overlap(ReservationOccurrence,
                                                    'start_dt', self.event.start_dt_local,
                                                    'end_dt', self.event.end_dt_local),
                                   Reservation.room_id == self.event.room.id,
                                   ~Room.is_deleted)
                           .join(Reservation)
                           .join(Room)
                           .has_rows())
            show_booking_warning = not has_overlap
        has_reference_types = ReferenceType.query.has_rows()
        has_event_labels = EventLabel.query.has_rows()
        show_draft_warning = (self.event.type_ == EventType.conference and
                              not contribution_settings.get(self.event, 'published') and
                              (TimetableEntry.query.with_parent(self.event).has_rows() or
                               Contribution.query.with_parent(self.event).has_rows()))
        return WPEventSettings.render_template('settings.html', self.event, 'settings',
                                               show_booking_warning=show_booking_warning,
                                               show_draft_warning=show_draft_warning,
                                               has_reference_types=has_reference_types,
                                               has_event_labels=has_event_labels)


class RHEditEventDataBase(RHManageEventBase):
    form_class = None
    section_name = None

    def render_form(self, form):
        return jsonify_form(form, footer_align_right=True)

    def render_settings_box(self):
        tpl = get_template_module('events/management/_settings.html')
        assert self.section_name
        has_reference_types = ReferenceType.query.has_rows()
        has_event_labels = EventLabel.query.has_rows()
        return tpl.render_event_settings(self.event, has_reference_types, has_event_labels,
                                         section=self.section_name, with_container=False)

    def jsonify_success(self):
        return jsonify_data(settings_box=self.render_settings_box(),
                            right_header=render_event_management_header_right(self.event))

    def _process(self):
        form = self.form_class(obj=self.event, event=self.event)
        if form.validate_on_submit():
            with flash_if_unregistered(self.event, lambda: self.event.person_links):
                update_event(self.event, **form.data)
            return self.jsonify_success()
        self.commit = False
        return self.render_form(form)


class RHEditEventData(RHEditEventDataBase):
    form_class = EventDataForm
    section_name = 'data'


class RHEditEventLocation(RHEditEventDataBase):
    form_class = EventLocationForm
    section_name = 'location'


class RHEditEventPersons(RHEditEventDataBase):
    form_class = EventPersonsForm
    section_name = 'persons'


class RHEditEventContactInfo(RHEditEventDataBase):
    form_class = EventContactInfoForm
    section_name = 'contact_info'

    def render_form(self, form):
        return jsonify_template('events/management/event_contact_info.html', form=form)


class RHEditEventClassification(RHEditEventDataBase):
    form_class = EventClassificationForm
    section_name = 'classification'


class RHEditEventDates(RHEditEventDataBase):
    section_name = 'dates'

    def _process(self):
        defaults = FormDefaults(self.event, update_timetable=True)
        form = EventDatesForm(obj=defaults, event=self.event)
        if form.validate_on_submit():
            with track_time_changes():
                update_event(self.event, **form.data)
            return self.jsonify_success()
        show_screen_dates = form.has_displayed_dates and (form.start_dt_override.data or form.end_dt_override.data)
        return jsonify_template('events/management/event_dates.html', form=form, show_screen_dates=show_screen_dates)
