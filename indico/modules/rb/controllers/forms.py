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

from datetime import datetime, timedelta
from functools import partial

from flask_wtf import Form
from wtforms import (
    BooleanField,
    Field,
    FieldList,
    IntegerField,
    SelectMultipleField,
    StringField,
    validators
)
from wtforms.ext.dateutil.fields import DateTimeField
from wtforms_alchemy import model_form_factory

from indico.core.errors import IndicoError
from indico.util.i18n import _

from ..models.reservations import Reservation, RepeatUnit


ModelForm = model_form_factory(Form, strip_string_fields=True)


def auto_datetime(diff=None):
    return (diff if diff else timedelta(0)) + datetime.utcnow()


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
    else:
        raise validators.ValidationError('Repeat Step only makes sense with Repeat Unit')


# TODO: minimum id should be a variable
class IndicoSelectMultipleField(Field):

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
        elif min(self.data) < -1:
            raise validators.StopValidation(_('Minimum id can be at least -1'))


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

    room_id_list = IndicoSelectMultipleField('Room ID List')

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
