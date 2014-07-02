# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

from datetime import datetime, date

from flask import session
from wtforms.ext.dateutil.fields import DateTimeField, DateField
from wtforms.fields.core import SelectMultipleField, StringField, BooleanField, RadioField, IntegerField
from wtforms.validators import DataRequired, InputRequired, NumberRange, ValidationError
from wtforms_components import TimeField
from wtforms.widgets.core import HiddenInput
from wtforms.fields.simple import HiddenField, TextAreaField, SubmitField

from indico.modules.rb.forms.base import IndicoForm, DataWrapper
from indico.modules.rb.forms.fields import IndicoQuerySelectMultipleCheckboxField
from indico.modules.rb.forms.validators import IndicoEmail, UsedIf
from indico.modules.rb.models.reservations import RepeatMapping, RepeatUnit
from indico.util.i18n import _


class BookingSearchForm(IndicoForm):
    __generated_data__ = ('start_dt', 'end_dt')

    room_ids = SelectMultipleField('Rooms', [DataRequired()], coerce=int)

    start_date = DateField('Start Date', [InputRequired()], parse_kwargs={'dayfirst': True})
    start_time = TimeField('Start Time', [InputRequired()])
    end_date = DateField('End Date', [InputRequired()], parse_kwargs={'dayfirst': True})
    end_time = TimeField('End Time', [InputRequired()])

    booked_for_name = StringField('Booked For Name')
    reason = StringField('Reason')

    is_only_mine = BooleanField('Only Mine')
    is_only_my_rooms = BooleanField('Only My Rooms')
    is_only_confirmed_bookings = BooleanField('Only Confirmed Bookings')
    is_only_pending_bookings = BooleanField('Only Prebookings')

    is_rejected = BooleanField('Is Rejected')
    is_cancelled = BooleanField('Is Cancelled')
    is_archived = BooleanField('Is Archived')

    uses_video_conference = BooleanField('Uses Video Conference')
    needs_video_conference_setup = BooleanField('Video Conference Setup Assistance')
    needs_general_assistance = BooleanField('General Assistance')

    @property
    def start_dt(self):
        return DataWrapper(datetime.combine(self.start_date.data, self.start_time.data))

    @property
    def end_dt(self):
        return DataWrapper(datetime.combine(self.end_date.data, self.end_time.data))


class NewBookingFormBase(IndicoForm):
    start_date = DateTimeField('Start date', validators=[InputRequired()], parse_kwargs={'dayfirst': True},
                               display_format='%d/%m/%Y %H:%M')
    end_date = DateTimeField('End date', validators=[InputRequired()], parse_kwargs={'dayfirst': True},
                             display_format='%d/%m/%Y %H:%M')
    repeat_unit = RadioField('Repeat unit', coerce=int, default=0, validators=[InputRequired()],
                             choices=[(0, _('Once')), (1, _('Daily')), (2, _('Weekly')), (3, _('Monthly'))])
    repeat_step = IntegerField('Repeat step', validators=[NumberRange(0, 3)], default=0)

    def validate_repeat_step(self, field):
        if (self.repeat_unit.data, self.repeat_step.data) not in RepeatMapping._mapping:
            raise ValidationError('Invalid repeat step')

    def validate_start_date(self, field):
        if field.data.date() < date.today() and not session.user.isAdmin():
            raise ValidationError(_('The start time cannot be in the past.'))

    def validate_end_date(self, field):
        start_date = self.start_date.data
        end_date = self.end_date.data
        if start_date.time() >= end_date.time():
            raise ValidationError('Invalid times')
        if self.repeat_unit.data == RepeatUnit.NEVER:
            field.data = datetime.combine(start_date.date(), field.data.time())
        elif start_date.date() >= end_date.date():
            raise ValidationError('Invalid period')


class NewBookingCriteriaForm(NewBookingFormBase):
    room_ids = SelectMultipleField('Rooms', [DataRequired()], coerce=int)
    flexible_dates_range = RadioField('Flexible days', coerce=int, default=0,
                                      choices=[(0, _('Exact')),
                                               (1, '&plusmn;{}'.format(_('1 day'))),
                                               (2, '&plusmn;{}'.format(_('2 days'))),
                                               (3, '&plusmn;{}'.format(_('3 days')))])

    def validate_flexible_dates_range(self, field):
        if self.repeat_unit.data == RepeatUnit.DAY:
            field.data = 0


class NewBookingPeriodForm(NewBookingFormBase):
    room_id = IntegerField('Room', [DataRequired()], widget=HiddenInput())


class NewBookingConfirmForm(NewBookingPeriodForm):
    booked_for_id = HiddenField(_('User'), [InputRequired()])
    booked_for_name = StringField()  # just for displaying
    contact_email = StringField(_('Email'), [InputRequired(), IndicoEmail(multi=True)])
    contact_phone = StringField(_('Telephone'))
    booking_reason = TextAreaField(_('Reason'), [DataRequired()])
    uses_video_conference = BooleanField(_('I will use videoconference equipment'))
    equipments = IndicoQuerySelectMultipleCheckboxField(_('VC equipment'), get_label=lambda x: x.name)
    needs_video_conference_setup = BooleanField(_('Request assistance for the startup of the videoconference session. '
                                                  'This support is usually performed remotely.'))
    needs_general_assistance = BooleanField(_('Request personal assistance for meeting startup'))
    submit_book = SubmitField(_('Create booking'))
    submit_prebook = SubmitField(_('Create pre-booking'))

    def validate_equipments(self, field):
        if field.data and not self.uses_video_conference.data:
            raise ValidationError('Video Conference equipment is not used.')
        elif not field.data and self.uses_video_conference.data:
            raise ValidationError('You need to select some Video Conference equipment')

    def validate_needs_video_conference_setup(self, field):
        if field.data and not self.uses_video_conference.data:
            raise ValidationError('Video Conference equipment is not used.')


class NewBookingSimpleForm(NewBookingConfirmForm):
    submit_check = SubmitField(_('Check conflicts'))
    booking_reason = TextAreaField(_('Reason'), [UsedIf(lambda form, field: not form.submit_check.data),
                                                 DataRequired()])


class ModifyBookingForm(NewBookingSimpleForm):
    submit_update = SubmitField(_('Update booking'))

    def __init__(self, *args, **kwargs):
        self._old_start_date = kwargs.pop('old_start_date')
        super(ModifyBookingForm, self).__init__(*args, **kwargs)
        del self.room_id
        del self.submit_book
        del self.submit_prebook

    def validate_start_date(self, field):
        if field.data.date() < self._old_start_date and not session.user.isAdmin():
            raise ValidationError(_('The start time cannot be moved into the paste.'))
