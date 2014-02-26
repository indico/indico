# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from datetime import datetime, time, timedelta
from functools import partial

from flask_wtf import Form
from wtforms import (
    BooleanField,
    DateField,
    Field,
    IntegerField,
    SelectField,
    StringField,
    validators,
)
from wtforms.validators import (
    any_of,
    optional,
    number_range,
    required
)
from wtforms.ext.dateutil.fields import DateTimeField
from wtforms_alchemy import model_form_factory

from indico.core.errors import IndicoError
from indico.util.i18n import _

from ..models.reservations import Reservation, RepeatUnit, RepeatMapping


ModelForm = model_form_factory(Form, strip_string_fields=True)

AVAILABILITY_VALUES = ['Available', 'Booked', 'Don\'t care']

def auto_datetime(diff=None):
    return (diff if diff else timedelta(0)) + datetime.utcnow()

def auto_date(specified_time):
    return datetime.combine(auto_datetime(), specified_time)

def repeat_step_check(form, field):
    if form.repeat_unit.validate(form):
        if form.repeat_unit.data == RepeatUnit.DAY:
            pass
        elif form.repeat_unit.data == RepeatUnit.WEEK:
            pass
        elif form.repeat_unit.data == RepeatUnit.MONTH:
            pass
        elif form.repeat_unit.data == RepeatUnit.YEAR:
            pass
    else:  # this part may be removed
        raise validators.ValidationError('Repeat Step only makes sense with Repeat Unit')


def repeatibility_check(form, field):
    if form.availability.validate(form):
        if form.availability.data == AVAILABILITY_VALUES[1]:
            if field.data >= 5:
                raise validators.ValidationError('Unrecognized repeatability')


class IndicoField(Field):

    def __init__(self, *args, **kw):
        self.parameter_name = kw.pop('parameter_name', None)
        super(IndicoField, self).__init__(*args, **kw)
        if not self.parameter_name:
            self.parameter_name = self.underscore_to_camel_case(self.name)

    def underscore_to_camel_case(self, s):
        ls = s.split('_')
        return ''.join(ls[:1] + [e.capitalize() for e in ls[1:]])

    def process_default(self, formdata, data):
        self.process_errors = []
        if data is None:
            try:
                data = self.default()
            except TypeError:
                data = self.default

        self.object_data = data

        try:
            self.process_data(data)
        except ValueError as e:
            self.process_errors.append(e.args[0])

    def process_filters(self):
        for filter in self.filters:
            try:
                self.data = filter(self.data)
            except ValueError as e:
                self.process_errors.append(e.args[0])

    def _process(self, formdata, data):
         if formdata:
            try:
                if self.parameter_name in formdata:
                    self.raw_data = formdata.getlist(self.parameter_name)
                elif self.name in formdata:
                    self.raw_data = formdata.getlist(self.name)
                else:
                    self.raw_data = []
                self.process_formdata(self.raw_data)
            except ValueError as e:
                self.process_errors.append(e.args[0])

    def process(self, formdata, data=None):
        self.process_default(formdata, data)
        self._process(formdata, data)
        self.process_filters()


class BooleanIndicoField(IndicoField, BooleanField):
    pass


class IntegerIndicoField(IndicoField, IntegerField):
    pass


class SelectIndicoField(IndicoField, SelectField):
    pass


class StringIndicoField(IndicoField, StringField):
    pass


class DateTimeIndicoField(IndicoField, DateTimeField):

    def process_formdata(self, raw_data):
        try:
            self.data = datetime.combine(datetime(*map(int, raw_data[:-1])),
                                         datetime.strptime(raw_data[-1], '%H:%M'))
        except:
            self.data = datetime(*map(int, raw_data))

    def _process(self, formdata, data=None):
        if formdata:
            try:
                try:
                    self.raw_data = [formdata.getlist(p)[0] for p in self.parameter_name]
                except KeyError:
                    camel_name = self.underscore_to_camel_case(self.name) in formdata
                    if camel_name in formdata:
                        self.raw_data = formdata.geetlist(self.name)
                    elif self.name in formdata:
                        self.raw_data = formdata.getlist(self.name)
                    else:
                        self.raw_data = []
                self.process_formdata(self.raw_data)
            except ValueError as e:
                self.process_errors.append(e.args[0])


class SelectMultipleCustomIndicoField(IndicoField):

    def __init__(self, *args, **kw):
        self.min_check = kw.pop('min_check', None)
        super(SelectMultipleCustomIndicoField, self).__init__(*args, **kw)

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = map(int, valuelist)
            except ValueError:
                self.data = []
                raise ValueError(_('Id must be integer'))
        else:
            self.data = []

    def pre_validate(self, form):
        if not self.data:
            raise validators.StopValidation(_('At least one integer id must be supplied'))
        elif self.min_check and min(self.data) < self.min_check:
            raise validators.StopValidation(_('Minimum id can be at least {}').format(self.min_check))


class MultipleCheckboxIndicoField(IndicoField):

    def __init__(self, prefix, *args, **kw):
        self.prefix = prefix
        super(MultipleCheckboxIndicoField, self).__init__(*args, **kw)

    def _process(self, formdata, data=None):
        if formdata:
            try:
                if self.prefix:
                    self.raw_data = [int(k.replace(self.prefix, '', 1))
                                     for k, _ in formdata.iteritems()
                                     if k.startswith(self.prefix)]
                else:
                    self.raw_data = []
                self.data = self.raw_data
            except ValueError as e:
                self.process_errors.append(e.args[0])


class BookingListForm(Form):

    is_only_pre_bookings = BooleanField('Only Prebookings', [validators.Optional()], default=False)
    is_only_bookings = BooleanField('Only Bookings', [validators.Optional()], default=False)
    is_only_mine = BooleanField('Only Mine', [validators.Optional()], default=False)
    is_only_my_rooms = BooleanField('Only My Rooms', [validators.Optional()], default=False)
    is_search = BooleanField('Search', [validators.Optional()], default=False)
    is_new_booking = BooleanField('New Booking', [validators.Optional()], default=False)
    is_auto = BooleanField('Auto', [validators.Optional()], default=False)
    is_today = BooleanField('Today', [validators.Optional()], default=False)
    is_archival = BooleanField('Is Archival', [validators.Optional()], default=False)
    is_heavy = BooleanField('Is Heavy', [validators.Optional()], default=False)

    flexible_dates_range = IntegerField('Flexible Date Range', [validators.Optional()], default=0)
    finish_date = BooleanField('Finish Date Exists', [validators.Optional()], default=True)

    repeat_unit = IntegerField('Repeat Unit', [validators.Optional(),
                               validators.NumberRange(min=RepeatUnit.NEVER, max=RepeatUnit.YEAR)],
                               default=RepeatUnit.NEVER)
    repeat_step = IntegerField('Repeat Step', [validators.Optional(), repeat_step_check],
                               default=0)

    room_id_list = SelectMultipleCustomIndicoField('Room ID List', min_check=-1)

    is_cancelled = BooleanField('Is Cancelled', [validators.optional()])
    is_rejected = BooleanField('Is Cancelled', [validators.optional()])

    booked_for_name = StringField('Booked For Name', [validators.optional()])
    reason = StringField('Reason', [validators.optional()])

    start_date = DateTimeField('Start Date', [validators.required()],
                               parse_kwargs={'dayfirst': True}, default=auto_datetime)
    end_date = DateTimeField('End Date', [validators.required()],
                             parse_kwargs={'dayfirst': True}, default=partial(auto_datetime, timedelta(7)))

    uses_video_conference = BooleanField('Uses Video Conference',
                                         [validators.optional()], default=False)
    needs_video_conference_setup = BooleanField('Video Conference Setup Assistance',
                                                [validators.optional()], default=False)
    needs_general_assistance = BooleanField('General Assistance',
                                            [validators.optional()], default=False)

    def __getattr__(self, attr):
        if attr == 'is_all_rooms':
            return self.room_id_list.data and -1 in self.room_id_list.data
        raise IndicoError('{} has no attribute: {}'.format(self.__class__.__name__, attr))


class BookingForm(ModelForm):
    class Meta:
        model = Reservation


class RoomListForm(Form):

    location_id = IntegerIndicoField(validators=[required(), number_range(min=1)],
                                     parameter_name='roomLocation')
    free_search = StringIndicoField(validators=[optional()])
    capacity = IntegerIndicoField(validators=[optional(), number_range(min=1)])
    equipments = MultipleCheckboxIndicoField('equipments_')

    availability = StringIndicoField(validators=[required(), any_of(values=AVAILABILITY_VALUES)],
                                     default='Don\'t care')
    repeatibility = IntegerIndicoField(validators=[optional(), repeatibility_check])

    includes_pending_blockings = BooleanIndicoField(validators=[required()], default=False,
                                                    parameter_name='includePendingBlockings')
    includes_pre_bookings = BooleanIndicoField(validators=[required()], default=False,
                                               parameter_name='includePrebookings')

    is_public = BooleanIndicoField(validators=[optional()], default=True,
                                   parameter_name='isReservable')
    is_only_my_rooms = BooleanIndicoField(validators=[optional()], default=False,
                                          parameter_name='onlyMy')
    is_auto_confirm = BooleanIndicoField(validators=[optional()], default=True,
                                         parameter_name='isAutoConfirmed')
    is_active = BooleanIndicoField(validators=[optional()], default=True)

    start_date = DateTimeIndicoField(validators=[optional()],
                                     parameter_name=('sYear', 'sMonth', 'sDay', 'sTime'),
                                     default=partial(auto_date, time(8, 30)))
    end_date = DateTimeIndicoField(validators=[optional()],
                                   parameter_name=('eYear', 'eMonth', 'eDay', 'eTime'),
                                   default=partial(auto_date, time(17, 30)))

    def __getattr__(self, attr):
        if attr == 'repeat':
            RepeatMapping.getNewMapping(self.repeatibility.data)
        raise IndicoError('{} has no attribute: {}'.format(self.__class__.__name__, attr))
