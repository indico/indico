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
from collections import defaultdict

from pytz import utc
from wtforms.fields import StringField, TextAreaField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, ValidationError, InputRequired, NumberRange
from wtforms_components import TimeField
from wtforms.widgets.html5 import NumberInput

from indico.modules.events.contributions.forms import ContributionForm
from indico.modules.events.sessions.forms import SessionBlockForm
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.modules.events.timetable.util import find_next_start_dt
from indico.web.forms.base import FormDefaults, IndicoForm, generated_data
from indico.web.forms.colors import get_colors
from indico.web.forms.fields import (TimeDeltaField, IndicoPalettePickerField, IndicoLocationField,
                                     IndicoSelectMultipleCheckboxField)
from indico.web.forms.util import get_form_field_names
from indico.web.forms.validators import MaxDuration, HiddenUnless
from indico.web.forms.widgets import SwitchWidget
from indico.util.i18n import _


class EntryFormMixin(object):
    _entry_type = None
    _default_duration = None
    _display_fields = None

    time = TimeField(_("Start time"), [InputRequired()])
    duration = TimeDeltaField(_("Duration"), [DataRequired(), MaxDuration(timedelta(hours=24))],
                              units=('minutes', 'hours'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs['event']
        self.session_block = kwargs.get('session_block')
        self.day = kwargs.pop('day')
        if self._default_duration is not None:
            kwargs['time'] = self._get_default_time()
            defaults = kwargs.get('obj') or FormDefaults()
            if 'duration' not in defaults:
                defaults.duration = self._default_duration
                kwargs['obj'] = defaults
        super(EntryFormMixin, self).__init__(*args, **kwargs)

    @property
    def data(self):
        data = super(EntryFormMixin, self).data
        del data['time']
        return data

    @generated_data
    def start_dt(self):
        if self.time.data:
            dt = datetime.combine(self.day, self.time.data)
            return self.event.tzinfo.localize(dt).astimezone(utc)

    def validate_duration(self, field):
        if not self.start_dt.data:
            return
        end_dt = self.start_dt.data + field.data
        if self.session_block and end_dt > self.session_block.end_dt:
            raise ValidationError(_("{} exceeds session block end time. Adjust start time or duration.")
                                  .format(self._entry_type.title.capitalize()))
        if end_dt > self.event.end_dt:
            raise ValidationError(_("{} exceeds event end time. Adjust start time or duration.")
                                  .format(self._entry_type.title.capitalize()))
        if end_dt.astimezone(self.event.tzinfo).date() > self.event.end_dt_local.date():
            raise ValidationError(_("{} exceeds current day. Adjust start time or duration.")
                                  .format(self._entry_type.title.capitalize()))

    def validate_time(self, field):
        if not field.data:
            return
        if self.session_block and self.start_dt.data < self.session_block.start_dt:
            raise ValidationError(_("{} can't be scheduled earlier than the session block start time.")
                                  .format(self._entry_type.title.capitalize()))
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
    description = TextAreaField(_("Description"))
    location_data = IndicoLocationField(_("Location"))
    colors = IndicoPalettePickerField(_('Colours'), color_list=get_colors())


class ContributionEntryForm(EntryFormMixin, ContributionForm):
    _entry_type = TimetableEntryType.CONTRIBUTION
    _default_duration = timedelta(minutes=20)
    _display_fields = ('title', 'description', 'type', 'time', 'duration', 'person_link_data', 'location_data',
                       'keywords', 'references')

    def __init__(self, *args, **kwargs):
        kwargs['to_schedule'] = kwargs.get('to_schedule', True)
        super(ContributionEntryForm, self).__init__(*args, **kwargs)


class SessionBlockEntryForm(EntryFormMixin, SessionBlockForm):
    _entry_type = TimetableEntryType.SESSION_BLOCK
    _default_duration = timedelta(minutes=60)
    _display_fields = ('title', 'time', 'duration', 'person_links', 'location_data')

    def validate_duration(self, field):
        super(SessionBlockEntryForm, self).validate_duration(field)
        if self.session_block:
            entry = self.session_block.timetable_entry
            end_dt = self.start_dt.data + field.data
            query = TimetableEntry.query.with_parent(entry).filter(TimetableEntry.end_dt > end_dt)
            if query.count():
                raise ValidationError(_("This duration is too short to fit the entries within."))


class BaseEntryForm(EntryFormMixin, IndicoForm):
    shift_later = BooleanField(_('Shift down'), widget=SwitchWidget(),
                               description=_("Shift down everything else that starts after this"))

    def __init__(self, *args, **kwargs):
        self._entry_type = kwargs.pop('entry').type
        super(BaseEntryForm, self).__init__(*args, **kwargs)


_DOCUMENT_SETTINGS_CHOICES = [('showCoverPage', _('Include cover page')),
                              ('showTableContents', _('Include table of contents')),
                              ('showSessionTOC', _('Show list of sessions in the table of contents'))]
_CONTRIBUTION_CHOICES = [('showContribId', _('Print the ID of each contribution')),
                         ('showAbstract', _('Print abstract content of all contributions')),
                         ('dontShowPosterAbstract', _('Do not print the abstract content for poster sessions')),
                         ('showLengthContribs', _('Include length of the contributions'))]
_SESSION_CHOICES = [('newPagePerSession', _('Print each session on a separate page')),
                    ('useSessionColorCodes', _('Use session color codes')),
                    ('showSessionDescription', _('Include session description')),
                    ('printDateCloseToSessions', _('Print the start date close to session title'))]
_VISIBLE_ENTRIES_CHOICES = [('showContribsAtConfLevel', _('Include top-level contributions')),
                            ('showBreaksAtConfLevel', _('Include top-level breaks'))]
_OTHER_CHOICES = [('showSpeakerTitle', _('Show speaker title')),
                  ('showSpeakerAffiliation', _('Show speaker affiliation'))]


class TimetablePDFExportForm(IndicoForm):
    _pdf_options_fields = {'pagesize', 'fontsize', 'firstPageNumber'}

    advanced = BooleanField(_("Advanced timetable"), widget=SwitchWidget(),
                            description=_("Advanced customization options"))
    document_settings = IndicoSelectMultipleCheckboxField(_('Document settings'), [HiddenUnless('advanced')],
                                                          choices=_DOCUMENT_SETTINGS_CHOICES)
    contribution_info = IndicoSelectMultipleCheckboxField(_('Contributions related info'), [HiddenUnless('advanced')],
                                                          choices=_CONTRIBUTION_CHOICES)
    session_info = IndicoSelectMultipleCheckboxField(_('Sessions related info'), [HiddenUnless('advanced')],
                                                     choices=_SESSION_CHOICES)
    visible_entries = IndicoSelectMultipleCheckboxField(_('Breaks and contributions'), [HiddenUnless('advanced')],
                                                        choices=_VISIBLE_ENTRIES_CHOICES)
    other = IndicoSelectMultipleCheckboxField(_('Miscellaneous'), choices=_OTHER_CHOICES)
    pagesize = SelectField(_('Page size'), choices=[('A0', 'A0'), ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'),
                                                    ('A4', 'A4'), ('A5', 'A5'), ('Letter', 'Letter')], default='A4')
    fontsize = SelectField(_('Font size'), choices=[('xxx-small', _('xxx-small')), ('xx-small', _('xx-small')),
                                                    ('x-small', _('x-small')), ('smaller', _('smaller')),
                                                    ('small', _('small')), ('normal', _('normal')),
                                                    ('large', _('large')), ('larger', _('larger'))], default='normal')
    firstPageNumber = IntegerField(_('Number for the first page'), [NumberRange(min=1)], default=1,
                                   widget=NumberInput(step=1))

    @property
    def data_for_format(self):
        if not self.advanced.data:
            fields = ('visible_entries',)
        else:
            fields = set(get_form_field_names(TimetablePDFExportForm)) - self._pdf_options_fields - {'csrf_token',
                                                                                                     'advanced'}
        return defaultdict(bool, {option: True for field in fields for option in getattr(self, field).data})
