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

from flask import redirect, session
from werkzeug.exceptions import Forbidden

from indico.core import signals
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.management.forms import (EventClassificationForm, EventContactInfoForm, EventDataForm,
                                                    EventDatesForm, EventLocationForm, EventPersonsForm)
from indico.modules.events.management.util import flash_if_unregistered
from indico.modules.events.management.views import WPEventSettings, render_event_management_header_right
from indico.modules.events.operations import update_event
from indico.modules.events.util import track_time_changes
from indico.util.signals import values_from_signal
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHEventSettings(RHManageEventBase):
    """Event settings dashboard"""

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
        return WPEventSettings.render_template('settings.html', self.event, 'settings')


class RHEditEventDataBase(RHManageEventBase):
    form_class = None
    section_name = None

    def render_form(self, form):
        return jsonify_form(form, footer_align_right=True)

    def render_settings_box(self):
        tpl = get_template_module('events/management/_settings.html')
        assert self.section_name
        return tpl.render_event_settings(self.event, section=self.section_name, with_container=False)

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
