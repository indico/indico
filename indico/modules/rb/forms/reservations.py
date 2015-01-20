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

from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.fields import IndicoQuerySelectMultipleCheckboxField
from indico.web.forms.validators import IndicoEmail, UsedIf
from indico.modules.rb.models.reservations import RepeatMapping, RepeatFrequency
from indico.util.i18n import _


class BookingSearchForm(IndicoForm):
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

    uses_vc = BooleanField('Uses Video Conference')
    needs_vc_assistance = BooleanField('Video Conference Setup Assistance')
    needs_assistance = BooleanField('General Assistance')

    @generated_data
    def start_dt(self):
        return datetime.combine(self.start_date.data, self.start_time.data)

    @generated_data
    def end_dt(self):
        return datetime.combine(self.end_date.data, self.end_time.data)


class NewBookingFormBase(IndicoForm):
    start_dt = DateTimeField('Start date', validators=[InputRequired()], parse_kwargs={'dayfirst': True},
                             display_format='%d/%m/%Y %H:%M')
    end_dt = DateTimeField('End date', validators=[InputRequired()], parse_kwargs={'dayfirst': True},
                           display_format='%d/%m/%Y %H:%M')
    repeat_frequency = RadioField('Repeat frequency', coerce=int, default=0, validators=[InputRequired()],
                                  choices=[(0, _(u'Once')), (1, _(u'Daily')), (2, _(u'Weekly')), (3, _(u'Monthly'))])
    repeat_interval = IntegerField('Repeat interval', validators=[NumberRange(0, 3)], default=0)

    def validate_repeat_interval(self, field):
        if (self.repeat_frequency.data, self.repeat_interval.data) not in RepeatMapping.mapping:
            raise ValidationError('Invalid repeat step')

    def validate_start_dt(self, field):
        if field.data.date() < date.today() and not session.user.isAdmin():
            raise ValidationError(_(u'The start time cannot be in the past.'))

    def validate_end_dt(self, field):
        start_dt = self.start_dt.data
        end_dt = self.end_dt.data
        if start_dt.time() >= end_dt.time():
            raise ValidationError('Invalid times')
        if self.repeat_frequency.data == RepeatFrequency.NEVER:
            field.data = datetime.combine(start_dt.date(), field.data.time())
        elif start_dt.date() >= end_dt.date():
            raise ValidationError('Invalid period')


class NewBookingCriteriaForm(NewBookingFormBase):
    room_ids = SelectMultipleField('Rooms', [DataRequired()], coerce=int)
    flexible_dates_range = RadioField('Flexible days', coerce=int, default=0,
                                      choices=[(0, _(u'Exact')),
                                               (1, '&plusmn;{}'.format(_(u'1 day'))),
                                               (2, '&plusmn;{}'.format(_(u'2 days'))),
                                               (3, '&plusmn;{}'.format(_(u'3 days')))])

    def validate_flexible_dates_range(self, field):
        if self.repeat_frequency.data == RepeatFrequency.DAY:
            field.data = 0


class NewBookingPeriodForm(NewBookingFormBase):
    room_id = IntegerField('Room', [DataRequired()], widget=HiddenInput())


class NewBookingConfirmForm(NewBookingPeriodForm):
    booked_for_id = HiddenField(_(u'User'), [InputRequired()])
    booked_for_name = StringField()  # just for displaying
    contact_email = StringField(_(u'Email'), [InputRequired(), IndicoEmail(multi=True)])
    contact_phone = StringField(_(u'Telephone'))
    booking_reason = TextAreaField(_(u'Reason'), [DataRequired()])
    uses_vc = BooleanField(_(u'I will use videoconference equipment'))
    used_equipment = IndicoQuerySelectMultipleCheckboxField(_(u'VC equipment'), get_label=lambda x: x.name)
    needs_vc_assistance = BooleanField(_(u'Request assistance for the startup of the videoconference session. '
                                         u'This support is usually performed remotely.'))
    needs_assistance = BooleanField(_(u'Request personal assistance for meeting startup'))
    submit_book = SubmitField(_(u'Create booking'))
    submit_prebook = SubmitField(_(u'Create pre-booking'))

    def validate_used_equipment(self, field):
        if field.data and not self.uses_vc.data:
            raise ValidationError(_(u'Video Conference equipment is not used.'))
        elif not field.data and self.uses_vc.data:
            raise ValidationError(_(u'You need to select some Video Conference equipment'))

    def validate_needs_vc_assistance(self, field):
        if field.data and not self.uses_vc.data:
            raise ValidationError(_(u'Video Conference equipment is not used.'))


class NewBookingSimpleForm(NewBookingConfirmForm):
    submit_check = SubmitField(_(u'Check conflicts'))
    booking_reason = TextAreaField(_(u'Reason'), [UsedIf(lambda form, field: not form.submit_check.data),
                                                  DataRequired()])


class ModifyBookingForm(NewBookingSimpleForm):
    submit_update = SubmitField(_(u'Update booking'))

    def __init__(self, *args, **kwargs):
        self._old_start_date = kwargs.pop('old_start_date')
        super(ModifyBookingForm, self).__init__(*args, **kwargs)
        del self.room_id
        del self.submit_book
        del self.submit_prebook

    def validate_start_dt(self, field):
        if field.data.date() < self._old_start_date and not session.user.isAdmin():
            raise ValidationError(_(u'The start time cannot be moved into the past.'))
