# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import redirect, session
from werkzeug.exceptions import Forbidden

from indico.core import signals
from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap
from indico.modules.categories.models.categories import InheritableConfigMode
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.management.forms import (EventClassificationForm, EventContactInfoForm, EventDataForm,
                                                    EventDatesForm, EventLanguagesForm, EventLocationForm,
                                                    EventPersonsForm)
from indico.modules.events.management.settings import global_event_settings
from indico.modules.events.management.util import flash_if_unregistered
from indico.modules.events.management.views import WPEventSettings, render_event_management_header_right
from indico.modules.events.models.labels import EventLabel
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.operations import update_event
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.util import should_show_draft_warning, track_location_changes, track_time_changes
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.util import rb_check_if_visible
from indico.util.i18n import _
from indico.util.signals import values_from_signal
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.forms.fields import IndicoStrictKeywordsField, IndicoTagListField
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


def _show_google_wallet_location_warning(event):
    if bool(event.address) == event.has_location_info:
        return False
    return (RegistrationForm.query.with_parent(event).filter(RegistrationForm.ticket_google_wallet).has_rows()
            and event.category.google_wallet_mode == InheritableConfigMode.enabled)


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
        show_booking_warning = False
        if (config.ENABLE_ROOMBOOKING and rb_check_if_visible(session.user)
                and not self.event.has_ended and self.event.room and not self.event.room_reservation_occurrence_links):
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
        return WPEventSettings.render_template('settings.html', self.event, 'settings',
                                               show_booking_warning=show_booking_warning,
                                               show_draft_warning=should_show_draft_warning(self.event),
                                               has_reference_types=has_reference_types,
                                               has_event_labels=has_event_labels,
                                               google_wallet_location_warning=_show_google_wallet_location_warning(
                                                   self.event))


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
        google_wallet_location_warning = _show_google_wallet_location_warning(self.event)
        return tpl.render_event_settings(self.event, has_reference_types, has_event_labels,
                                         google_wallet_location_warning,
                                         section=self.section_name, with_container=False)

    def jsonify_success(self):
        return jsonify_data(settings_box=self.render_settings_box(),
                            right_header=render_event_management_header_right(self.event))

    def _update(self, form_data):
        update_event(self.event, **form_data)

    def _process(self):
        form = self.form_class(obj=self.event, event=self.event)
        if form.validate_on_submit():
            with flash_if_unregistered(self.event, lambda: self.event.person_links):
                self._update(form.data)
            return self.jsonify_success()
        self.commit = False
        return self.render_form(form)


class RHEditEventData(RHEditEventDataBase):
    form_class = EventDataForm
    section_name = 'data'


class RHEditEventLocation(RHEditEventDataBase):
    form_class = EventLocationForm
    section_name = 'location'

    def _update(self, form_data):
        with track_location_changes():
            return super()._update(form_data)


class RHEditEventPersons(RHEditEventDataBase):
    form_class = EventPersonsForm
    section_name = 'persons'


class RHEditEventContactInfo(RHEditEventDataBase):
    form_class = EventContactInfoForm
    section_name = 'contact_info'

    def render_form(self, form):
        return jsonify_template('events/management/event_contact_info.html', form=form)


class RHEditEventClassification(RHEditEventDataBase):
    section_name = 'classification'

    @property
    def form_class(self):
        if allowed_keywords := global_event_settings.get('allowed_keywords'):
            choices = [{'id': kw, 'name': kw} for kw in (set(allowed_keywords) | set(self.event.keywords))]
            keywords = IndicoStrictKeywordsField(_('Keywords'), choices=choices)
        else:
            keywords = IndicoTagListField(_('Keywords'))
        return type('_EventClassificationForm', (EventClassificationForm,), {'keywords': keywords})


class RHEditEventLanguages(RHEditEventDataBase):
    form_class = EventLanguagesForm
    section_name = 'languages'


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
