# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime, time
from uuid import uuid4

from dateutil.relativedelta import relativedelta
from flask import flash, jsonify, redirect, render_template, request, session
from markupsafe import Markup
from pytz import common_timezones_set, timezone
from webargs import fields
from werkzeug.utils import cached_property

from indico.core.cache import make_scoped_cache
from indico.core.config import config
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.categories import Category
from indico.modules.categories.util import can_create_unlisted_events
from indico.modules.events.forms import EventCreationForm, LectureCreationForm
from indico.modules.events.models.events import EventType
from indico.modules.events.models.persons import EventPerson, EventPersonLink
from indico.modules.events.models.series import EventSeries
from indico.modules.events.notifications import notify_event_creation
from indico.modules.events.operations import create_event
from indico.modules.rb import rb_settings
from indico.modules.rb.util import rb_check_user_access
from indico.util.date_time import now_utc
from indico.util.iterables import materialize_iterable
from indico.util.marshmallow import NaiveDateTime
from indico.web.args import use_kwargs
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.rh import RH, RHProtected
from indico.web.util import jsonify_data, jsonify_template, url_for_index


prepared_event_data_store = make_scoped_cache('event-preparation')


class RHCreateEvent(RHProtected):
    """Create a new event."""

    def _process_args(self):
        self.event_type = EventType[request.view_args['event_type']]
        self.root_category = Category.get_root()

    def _has_only_subcategories(self, category):
        return category.has_children and not category.has_events

    @cached_property
    def _default_category(self):
        try:
            category_id = int(request.args['category_id'])
        except (ValueError, KeyError):
            return None if self._has_only_subcategories(self.root_category) else self.root_category

        category = Category.get(category_id, is_deleted=False)
        if category and category.is_root and self._has_only_subcategories(category):
            return None
        else:
            return category

    def _get_prepared_data(self):
        try:
            data = prepared_event_data_store.get(request.args['event_uuid'])
        except KeyError:
            return None
        if not data:
            return None
        title = data['title']
        start_dt = data['start_dt']
        end_dt = start_dt + relativedelta(minutes=data['duration'])
        return start_dt, end_dt, title

    def _get_form_defaults(self):
        category = self._default_category
        tzinfo = timezone(config.DEFAULT_TIMEZONE)
        if category is not None:
            tzinfo = timezone(category.timezone)

        prepared_data = self._get_prepared_data()
        if prepared_data:
            start_dt, end_dt, title = prepared_data
        else:
            title = ''
            # try to find good dates/times
            now = now_utc(exact=False)
            start_dt = now + relativedelta(hours=1, minute=0)
            if start_dt.astimezone(tzinfo).time() > time(18):
                start_dt = tzinfo.localize(datetime.combine(now.date() + relativedelta(days=1), time(9)))
            end_dt = start_dt + relativedelta(hours=2)

        # XXX: Do not provide a default value for protection_mode. It is selected via JavaScript code
        # once a category has been selected.
        return FormDefaults(title=title,
                            category=category,
                            timezone=tzinfo.zone, start_dt=start_dt, end_dt=end_dt,
                            occurrences=[(start_dt, end_dt - start_dt)],
                            location_data={'inheriting': False},
                            create_booking=False)

    def _create_event(self, data):
        data = data.copy()
        return create_event(data.pop('category', None), self.event_type, data)

    @materialize_iterable()
    def _create_series(self, data):
        @materialize_iterable(dict)
        def _copy_person_link_data(link_data):
            # Copy person link data since we would otherwise end up
            # adding the EventPersons of the first event in all other
            # events of the series.
            for link, submitter in link_data.items():
                link_copy = EventPersonLink(**{col: getattr(link, col)
                                               for col in get_simple_column_attrs(EventPersonLink)})
                link_copy.person = EventPerson(**{col: getattr(link.person, col)
                                                  for col in get_simple_column_attrs(EventPerson)})
                link_copy.person.user = link.person.user
                yield link_copy, submitter

        occurrences = data.pop('occurrences')
        if len(occurrences) > 1:
            data['series'] = EventSeries()
        for occ in occurrences:
            start_dt = occ[0]
            end_dt = start_dt + occ[1]
            yield self._create_event(dict(data,
                                          person_link_data=_copy_person_link_data(data['person_link_data']),
                                          start_dt=start_dt, end_dt=end_dt))

    def _process(self):
        if not request.is_xhr:
            return redirect(url_for_index(_anchor=f'create-event:{self.event_type.name}'))
        form_cls = LectureCreationForm if self.event_type == EventType.lecture else EventCreationForm
        form = form_cls(obj=self._get_form_defaults(), prefix='event-creation-')

        if form.validate_on_submit():
            data = form.data
            listing = data.pop('listing')
            if not listing and can_create_unlisted_events(session.user):
                del data['category']

            if self.event_type == EventType.lecture:
                events = self._create_series(data)
                event = events[0]
                if len(events) > 1:
                    flash(Markup(render_template('events/series_created_msg.html', events=events)), 'info')
                notify_event_creation(event, occurrences=events)
            else:
                event = self._create_event(data)
                notify_event_creation(event)
            return jsonify_data(flash=False, redirect=url_for('event_management.settings', event))
        check_room_availability = rb_check_user_access(session.user) and config.ENABLE_ROOMBOOKING
        rb_excluded_categories = [c.id for c in rb_settings.get('excluded_categories')]
        category = self._default_category
        can_create_events = category.can_create_events(session.user) if category else True
        return jsonify_template('events/forms/event_creation_form.html', form=form, fields=form._field_order,
                                event_type=self.event_type.name, single_category=(not self.root_category.has_children),
                                check_room_availability=check_room_availability,
                                rb_excluded_categories=rb_excluded_categories,
                                can_create_events=can_create_events,
                                can_create_unlisted_events=can_create_unlisted_events(session.user))


class RHPrepareEvent(RH):
    """Prepare the creation of an event with some data."""

    CSRF_ENABLED = False

    @use_kwargs({
        'title': fields.String(required=True),
        'start_dt': NaiveDateTime(required=True),
        'tz': fields.String(load_default=config.DEFAULT_TIMEZONE, validate=lambda v: v in common_timezones_set),
        'duration': fields.Integer(required=True, validate=lambda v: v > 0),
        'event_type': fields.String(load_default='meeting'),
    })
    def _process(self, title, start_dt, tz, duration, event_type):
        event_key = str(uuid4())
        start_dt = timezone(tz).localize(start_dt)
        prepared_event_data_store.set(
            event_key,
            {
                'title': title,
                'start_dt': start_dt,
                'duration': duration,
                'event_type': event_type,
            },
            3600
        )
        return jsonify(url=url_for_index(_external=True, _anchor=f'create-event:meeting::{event_key}'))
