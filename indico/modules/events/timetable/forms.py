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

from indico.modules.events.contributions.forms import ContributionForm
from indico.modules.events.sessions.forms import SessionBlockForm
from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.modules.events.timetable.util import find_next_start_dt
from indico.web.forms.base import FormDefaults, IndicoForm, generated_data
from indico.web.forms.colors import get_colors
from indico.web.forms.fields import TimeDeltaField, IndicoPalettePickerField, IndicoLocationField
from indico.web.forms.validators import MaxDuration
from indico.util.i18n import _


class EntryFormMixin(object):
    _entry_type = None
    _default_duration = None
    _display_fields = None

    time = TimeField(_("Time"), [DataRequired()])
    duration = TimeDeltaField(_("Duration"), [DataRequired(), MaxDuration(timedelta(hours=24))],
                              units=('minutes', 'hours'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs['event']
        self.session_block = kwargs.pop('session_block', None)
        self.day = kwargs.pop('day')
        kwargs['time'] = self._get_default_time()
        defaults = kwargs.get('obj') or FormDefaults()
        if 'duration' not in defaults:
            defaults.duration = self._default_duration
            kwargs['obj'] = defaults
        super(EntryFormMixin, self).__init__(*args, **kwargs)
        self.time.description = _("Time when the {} will be scheduled.").format(self._entry_type.title.lower())
        self.duration.description = _("The duration of the break").format(self._entry_type.title.lower())

    @property
    def data(self):
        data = super(EntryFormMixin, self).data
        del data['time']
        return data

    @generated_data
    def start_dt(self):
        dt = datetime.combine(self.day, self.time.data)
        return self.event.tzinfo.localize(dt).astimezone(utc)

    def validate_duration(self, field):
        end_dt = self.start_dt.data + field.data
        if end_dt > self.event.end_dt:
            raise ValidationError(_("{} exceeds event end time. Adjust start time or duration.")
                                  .format(self._entry_type.title.capitalize()))
        if end_dt.astimezone(self.event.tzinfo).date() > self.event.end_dt_local.date():
            raise ValidationError(_("{} exceeds current day. Adjust start time or duration.")
                                  .format(self._entry_type.title.capitalize()))

    def validate_time(self, field):
        if self.day == self.event.start_dt_local.date() and field.data < self.event.start_dt_local.time():
            raise ValidationError(_("{} can't be scheduled earlier than the event start time.")
                                  .format(self._entry_type.title.capitalize()))

    def _get_default_time(self):
        start_dt = find_next_start_dt(self._default_duration,
                                      obj=self.session_block or self.event,
                                      day=None if self.session_block else self.day)
        return start_dt.astimezone(self.event.tzinfo).time() if start_dt else None


class BreakEntryForm(EntryFormMixin, IndicoForm):
    _entry_type = TimetableEntryType.BREAK
    _default_duration = timedelta(minutes=20)
    _display_fields = ('title', 'description', 'time', 'duration', 'location_data', 'colors')

    title = StringField(_("Title"), [DataRequired()])
    description = TextAreaField(_("Description"), description=_("Text describing the break."))
    location_data = IndicoLocationField(_("Location"),
                                        description=_("The physical location where the break takes place."))
    colors = IndicoPalettePickerField(_('Colours'), color_list=get_colors(),
                                      description=_('Specify text and background colours for the break.'))


class ContributionEntryForm(EntryFormMixin, ContributionForm):
    _entry_type = TimetableEntryType.CONTRIBUTION
    _default_duration = timedelta(minutes=20)
    _display_fields = ('title', 'description', 'type', 'time', 'duration', 'person_link_data', 'location_data',
                       'keywords', 'references')

    time = TimeField(_("Time"), description=_("Time when the contribution will be scheduled."))
    duration = TimeDeltaField(_("Duration"), [DataRequired(), MaxDuration(timedelta(hours=24))],
                              default=timedelta(minutes=60), units=('minutes', 'hours'),
                              description=_("The duration of the contribution."))

    def __init__(self, *args, **kwargs):
        kwargs['to_schedule'] = kwargs.get('to_schedule', True)
        super(ContributionEntryForm, self).__init__(*args, **kwargs)


class SessionBlockEntryForm(EntryFormMixin, SessionBlockForm):
    _entry_type = TimetableEntryType.SESSION_BLOCK
    _default_duration = timedelta(minutes=60)
    _display_fields = ('title', 'time', 'duration', 'person_links', 'location_data')


class BaseEntryForm(EntryFormMixin, IndicoForm):
    def __init__(self, *args, **kwargs):
        self.event = kwargs['event']
        self.day = kwargs.pop('day')
        self.item = kwargs.pop('item')
        super(EntryFormMixin, self).__init__(*args, **kwargs)
        self.time.description = _("Time when the {} will be scheduled.").format(self.item.title.lower())
        self.duration.description = _("The duration of the {}").format(self.item.title.lower())
