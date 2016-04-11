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
from wtforms.fields import StringField, TextAreaField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, ValidationError, InputRequired, NumberRange
from wtforms_components import TimeField
from wtforms.widgets.html5 import NumberInput

from indico.modules.events.contributions.forms import ContributionForm
from indico.modules.events.sessions.forms import SessionBlockForm
from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.modules.events.timetable.util import find_next_start_dt
from indico.web.forms.base import FormDefaults, IndicoForm, generated_data
from indico.web.forms.colors import get_colors
from indico.web.forms.fields import TimeDeltaField, IndicoPalettePickerField, IndicoLocationField
from indico.web.forms.util import get_form_field_names
from indico.web.forms.validators import MaxDuration, HiddenUnless
from indico.web.forms.widgets import SwitchWidget
from indico.util.i18n import _


class EntryFormMixin(object):
    _entry_type = None
    _default_duration = None
    _display_fields = None

    time = TimeField(_("Time"), [InputRequired()])
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

    def __init__(self, *args, **kwargs):
        kwargs['to_schedule'] = kwargs.get('to_schedule', True)
        super(ContributionEntryForm, self).__init__(*args, **kwargs)


class SessionBlockEntryForm(EntryFormMixin, SessionBlockForm):
    _entry_type = TimetableEntryType.SESSION_BLOCK
    _default_duration = timedelta(minutes=60)
    _display_fields = ('title', 'time', 'duration', 'person_links', 'location_data')


class BaseEntryForm(EntryFormMixin, IndicoForm):
    def __init__(self, *args, **kwargs):
        self._entry_type = kwargs.pop('entry').type
        super(BaseEntryForm, self).__init__(*args, **kwargs)


class LegacyExportTimetablePDFForm(IndicoForm):
    _pdf_options_fields = {'pagesize', 'fontsize', 'firstPageNumber'}

    simplified = BooleanField(_('Simplified Timetable'), widget=SwitchWidget(),
                              description=_("Enable to get a simplified version of the timetable"))

    showCoverPage = BooleanField(_('Cover page'), [HiddenUnless('simplified', False)], default=True,
                                 description=_('Whether to include cover page'))
    showTableContents = BooleanField(_('Table of contents'), [HiddenUnless('simplified', False)], default=True,
                                     description=_('Whether to include table of contents'))
    showSessionTOC = BooleanField(_('Show sessions'), [HiddenUnless('showTableContents'),
                                                       HiddenUnless('simplified', False)], default=True,
                                  description=_('Whether to show the sessions inside the table of contents'))
    showContribId = BooleanField(_('Contribution ID'), [HiddenUnless('simplified', False)], default=True,
                                 description=_('Whether to print the ID of each contribution'))
    showAbstract = BooleanField(_('Abstract content'), [HiddenUnless('simplified', False)],
                                description=_('Print abstract content of all the contributions '))
    dontShowPosterAbstract = BooleanField(_('Include abstract info'), [HiddenUnless('showAbstract')],
                                          description=_('Do not print the abstract content for poster sessions'))
    showLengthContribs = BooleanField(_('Contribution Length'), [HiddenUnless('simplified', False)],
                                      description=_('Whether to include contribution length'))
    showSpeakerTitle = BooleanField(_('Speaker title'), [HiddenUnless('simplified', False)], default=True,
                                    description=_('Whether to include speaker title'))
    showSpeakerAffiliation = BooleanField(_('Speaker affiliation'), [HiddenUnless('simplified', False)],
                                          description=_('Whether to include speaker affiliation'))
    newPagePerSession = BooleanField(_('New page for session'), [HiddenUnless('simplified', False)],
                                     description=_('Print each session on separate page'))
    useSessionColorCodes = BooleanField(_('Session colors'), [HiddenUnless('simplified', False)], default=True,
                                        description=_('Whether to use session color codes'))
    showSessionDescription = BooleanField(_('Session description'), [HiddenUnless('simplified', False)], default=True,
                                          description=_("Whether to include session description"))
    showContribsAtConfLevel = BooleanField(_('Top-level contribution'),
                                           description=_("Whether to include contributions that are not inside any "
                                                         "session"))
    showBreaksAtConfLevel = BooleanField(_('Top-level breaks'),
                                         description=_('Whether to include breaks that are not inside any session'))
    printDateCloseToSessions = BooleanField(_('Start date'), [HiddenUnless('simplified', False)],
                                            description=_('Print the start date close to session title'))
    pagesize = SelectField(_('Page size'), choices=[('A0', 'A0'), ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'),
                                                    ('A4', 'A4'), ('A5', 'A5'), ('Letter', 'Letter')], default='A4')
    fontsize = SelectField(_('Font size'), choices=[('xxx-small', _('xxx-small')), ('xx-small', _('xx-small')),
                                                    ('x-small', _('x-small')), ('smaller', _('smaller')),
                                                    ('small', _('small')), ('normal', _('normal')), ('large', _('large')),
                                                    ('larger', _('larger'))], default='normal')
    firstPageNumber = IntegerField(_('Number for the first page'), [NumberRange(min=1)], default=1,
                                   widget=NumberInput(step=1))

    @property
    def data_for_format(self):
        if self.simplified.data:
            fields = ('showContribsAtConfLevel', 'showBreaksAtConfLevel')
        else:
            fields = set(get_form_field_names(LegacyExportTimetablePDFForm)) - self._pdf_options_fields - {'csrf_token'}
        return {x: getattr(self, x).data for x in fields}
