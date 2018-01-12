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

from datetime import datetime, timedelta

from flask import request
from pytz import utc
from wtforms.fields import BooleanField, HiddenField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, NumberRange, ValidationError
from wtforms.widgets.html5 import NumberInput
from wtforms_components import TimeField

from indico.modules.events.contributions.forms import ContributionForm
from indico.modules.events.sessions.forms import SessionBlockForm
from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.modules.events.timetable.util import find_next_start_dt
from indico.util.i18n import _
from indico.web.forms.base import FormDefaults, IndicoForm, generated_data
from indico.web.forms.colors import get_colors
from indico.web.forms.fields import (IndicoLocationField, IndicoPalettePickerField,
                                     IndicoSelectMultipleCheckboxBooleanField, TimeDeltaField)
from indico.web.forms.util import get_form_field_names
from indico.web.forms.validators import HiddenUnless, MaxDuration
from indico.web.forms.widgets import SwitchWidget


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
            kwargs.setdefault('time', self._get_default_time())
            defaults = kwargs.get('obj') or FormDefaults()
            if 'duration' not in defaults:
                if self._entry_type == TimetableEntryType.CONTRIBUTION and self.session_block:
                    defaults.duration = self.session_block.session.default_contribution_duration
                else:
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
        if self.time.data is not None:
            dt = datetime.combine(self.day, self.time.data)
            return self.event.tzinfo.localize(dt).astimezone(utc)

    def validate_duration(self, field):
        if not self.start_dt.data:
            return
        end_dt = self.start_dt.data + field.data
        if end_dt.astimezone(self.event.tzinfo).date() > self.event.end_dt_local.date():
            raise ValidationError(_("{} exceeds current day. Adjust start time or duration.")
                                  .format(self._entry_type.title.capitalize()))

    def _get_default_time(self):
        if self.session_block:
            # inside a block we suggest right after the latest contribution
            # or fall back to the block start time if it's empty
            entry = self.session_block.timetable_entry
            start_dt = max(x.end_dt for x in entry.children) if entry.children else entry.start_dt
        else:
            # outside a block we find the first slot where a contribution would fit
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

    @staticmethod
    def _validate_duration(entry, field, start_dt):
        if entry.children and start_dt.data is not None:
            end_dt = start_dt.data + field.data
            if end_dt < max(x.end_dt for x in entry.children):
                raise ValidationError(_("This duration is too short to fit the entries within."))

    def validate_duration(self, field):
        super(SessionBlockEntryForm, self).validate_duration(field)
        if self.session_block and self.start_dt.data:
            self._validate_duration(self.session_block.timetable_entry, field, self.start_dt)


class BaseEntryForm(EntryFormMixin, IndicoForm):
    shift_later = BooleanField(_('Shift down'), widget=SwitchWidget(),
                               description=_("Shift down everything else that starts after this"))

    def __init__(self, *args, **kwargs):
        self.entry = kwargs.pop('entry')
        self._entry_type = self.entry.type
        super(BaseEntryForm, self).__init__(*args, **kwargs)

    def validate_duration(self, field):
        super(BaseEntryForm, self).validate_duration(field)
        if self.entry.type == TimetableEntryType.SESSION_BLOCK and self.entry.children:
            SessionBlockEntryForm._validate_duration(self.entry, field, self.start_dt)


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
    document_settings = IndicoSelectMultipleCheckboxBooleanField(_('Document settings'), [HiddenUnless('advanced')],
                                                                 choices=_DOCUMENT_SETTINGS_CHOICES)
    contribution_info = IndicoSelectMultipleCheckboxBooleanField(_('Contributions related info'),
                                                                 [HiddenUnless('advanced')],
                                                                 choices=_CONTRIBUTION_CHOICES)
    session_info = IndicoSelectMultipleCheckboxBooleanField(_('Sessions related info'), [HiddenUnless('advanced')],
                                                            choices=_SESSION_CHOICES)
    visible_entries = IndicoSelectMultipleCheckboxBooleanField(_('Breaks and contributions'),
                                                               [HiddenUnless('advanced')],
                                                               choices=_VISIBLE_ENTRIES_CHOICES)
    other = IndicoSelectMultipleCheckboxBooleanField(_('Miscellaneous'), choices=_OTHER_CHOICES)
    pagesize = SelectField(_('Page size'), choices=[('A0', 'A0'), ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'),
                                                    ('A4', 'A4'), ('A5', 'A5'), ('Letter', 'Letter')], default='A4')
    fontsize = SelectField(_('Font size'), choices=[('xxx-small', _('xxx-small')), ('xx-small', _('xx-small')),
                                                    ('x-small', _('x-small')), ('smaller', _('smaller')),
                                                    ('small', _('small')), ('normal', _('normal')),
                                                    ('large', _('large')), ('larger', _('larger'))], default='normal')
    firstPageNumber = IntegerField(_('Number for the first page'), [NumberRange(min=1)], default=1,
                                   widget=NumberInput(step=1))
    submitted = HiddenField()

    def is_submitted(self):
        return 'submitted' in request.args

    @property
    def data_for_format(self):
        if not self.advanced.data:
            fields = ('visible_entries',)
        else:
            fields = set(get_form_field_names(TimetablePDFExportForm)) - self._pdf_options_fields - {'csrf_token',
                                                                                                     'advanced'}
        data = {}
        for fieldname in fields:
            data.update(getattr(self, fieldname).data)
        return data
