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

from __future__ import unicode_literals

from datetime import datetime, timedelta

from pytz import utc
from wtforms.fields import StringField, TextAreaField
from wtforms.validators import DataRequired, ValidationError
from wtforms_components import TimeField

from indico.modules.events.timetable.util import find_earliest_gap
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.colors import get_colors
from indico.web.forms.fields import TimeDeltaField, IndicoPalettePickerField, IndicoLocationField
from indico.web.forms.validators import MaxDuration
from indico.util.i18n import _


class BreakEntryForm(IndicoForm):
    title = StringField(_("Title"), [DataRequired()])
    description = TextAreaField(_("Description"), description=_("Text describing the break."))
    time = TimeField(_("Time"), description=_("Time where the break will be scheduled."))
    duration = TimeDeltaField(_("Duration"), [DataRequired(), MaxDuration(timedelta(hours=24))],
                              default=timedelta(minutes=20), units=('minutes', 'hours'),
                              description=_("The duration of the break"))
    location_data = IndicoLocationField(_("Location"),
                                        description=_("The physical location where the break takes place."))
    colors = IndicoPalettePickerField(_('Colours'), color_list=get_colors(),
                                      description=_('Specify text and background colours for the break.'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.day = kwargs.pop('day')
        self.time.kwargs['default'] = find_earliest_gap(self.event, self.day, duration=timedelta(minutes=20)).time()
        super(BreakEntryForm, self).__init__(*args, **kwargs)

    @property
    def data(self):
        data = super(BreakEntryForm, self).data
        del data['time']
        return data

    @generated_data
    def start_dt(self):
        dt = datetime.combine(self.day, self.time.data)
        return self.event.tzinfo.localize(dt).astimezone(utc)

    def validate_duration(self, field):
        end_dt = self.start_dt.data + field.data
        if end_dt > self.event.end_dt:
            raise ValidationError(_("With current time and duration the break ends after the event."))
        tzinfo = self.event.tzinfo
        if end_dt.astimezone(tzinfo).date() > self.event.end_dt.astimezone(tzinfo).date():
            raise ValidationError(_("With current time and duration the break can't fit on this day."))

    def validate_time(self, field):
        tzinfo = self.event.tzinfo
        if (self.day == self.event.start_dt.astimezone(tzinfo).date()
                and field.data < self.event.start_dt.astimezone(tzinfo).time()):
            raise ValidationError(_("The break can't be scheduled earlier than the event start time."))
