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

from datetime import datetime, time

from dateutil.relativedelta import relativedelta
from flask import flash, redirect, render_template, request
from markupsafe import Markup
from pytz import timezone
from werkzeug.utils import cached_property

from indico.core.config import config
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.categories import Category
from indico.modules.events.forms import EventCreationForm, LectureCreationForm
from indico.modules.events.models.events import EventType
from indico.modules.events.models.persons import EventPerson, EventPersonLink
from indico.modules.events.models.series import EventSeries
from indico.modules.events.notifications import notify_event_creation
from indico.modules.events.operations import create_event
from indico.util.date_time import now_utc
from indico.util.struct.iterables import materialize_iterable
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.rh import RHProtected
from indico.web.util import jsonify_data, jsonify_template, url_for_index


class RHCreateEvent(RHProtected):
    """Create a new event"""

    def _process_args(self):
        self.event_type = EventType[request.view_args['event_type']]
        self.root_category = Category.get_root()
        self.single_category = not self.root_category.children

    @cached_property
    def _default_category(self):
        try:
            category_id = int(request.args['category_id'])
        except (ValueError, KeyError):
            return self.root_category if self.single_category else None
        else:
            return Category.get(category_id, is_deleted=False)

    def _get_form_defaults(self):
        category = self._default_category
        tzinfo = timezone(config.DEFAULT_TIMEZONE)
        if category is not None:
            tzinfo = timezone(category.timezone)

        # try to find good dates/times
        now = now_utc(exact=False)
        start_dt = now + relativedelta(hours=1, minute=0)
        if start_dt.astimezone(tzinfo).time() > time(18):
            start_dt = tzinfo.localize(datetime.combine(now.date() + relativedelta(days=1), time(9)))
        end_dt = start_dt + relativedelta(hours=2)

        # XXX: Do not provide a default value for protection_mode. It is selected via JavaScript code
        # once a category has been selected.
        return FormDefaults(category=category,
                            timezone=tzinfo.zone, start_dt=start_dt, end_dt=end_dt,
                            occurrences=[(start_dt, end_dt - start_dt)],
                            location_data={'inheriting': False})

    def _create_event(self, data):
        data = data.copy()
        return create_event(data.pop('category'), self.event_type, data)

    @materialize_iterable()
    def _create_series(self, data):
        @materialize_iterable(dict)
        def _copy_person_link_data(link_data):
            # Copy person link data since we would otherwise end up
            # adding the EventPersons of the first event in all other
            # events of the series.
            for link, submitter in link_data.iteritems():
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
            return redirect(url_for_index(_anchor='create-event:{}'.format(self.event_type.name)))
        form_cls = LectureCreationForm if self.event_type == EventType.lecture else EventCreationForm
        form = form_cls(obj=self._get_form_defaults(), prefix='event-creation-')
        if form.validate_on_submit():
            if self.event_type == EventType.lecture:
                events = self._create_series(form.data)
                event = events[0]
                if len(events) > 1:
                    flash(Markup(render_template('events/series_created_msg.html', events=events)), 'info')
                notify_event_creation(event, occurrences=events)
            else:
                event = self._create_event(form.data)
                notify_event_creation(event)
            return jsonify_data(flash=False, redirect=url_for('event_management.settings', event))
        return jsonify_template('events/forms/event_creation_form.html', form=form, fields=form._field_order,
                                event_type=self.event_type.name, single_category=self.single_category)
