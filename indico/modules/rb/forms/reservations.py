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

from datetime import date, datetime

from flask import session
from wtforms.ext.dateutil.fields import DateTimeField
from wtforms.fields.core import BooleanField, IntegerField, RadioField, SelectMultipleField, StringField
from wtforms.fields.simple import SubmitField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, NumberRange, ValidationError
from wtforms.widgets.core import HiddenInput
from wtforms_components import TimeField

from indico.modules.rb.models.reservations import RepeatFrequency, RepeatMapping
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.fields import IndicoDateField, IndicoQuerySelectMultipleCheckboxField, PrincipalField
from indico.web.forms.validators import HiddenUnless, UsedIf


class BookingSearchForm(IndicoForm):
    room_ids = SelectMultipleField('Rooms', [DataRequired()], coerce=int)

    start_date = IndicoDateField('Start Date', [InputRequired()])
    start_time = TimeField('Start Time', [InputRequired()])
    end_date = IndicoDateField('End Date', [InputRequired()])
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

    uses_vc = BooleanField(_('Uses Videoconference'))
    needs_vc_assistance = BooleanField(_('Videoconference Setup Assistance'))
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
                                  choices=[(0, _('Once')), (1, _('Daily')), (2, _('Weekly')), (3, _('Monthly'))])
    repeat_interval = IntegerField('Repeat interval', validators=[NumberRange(0, 3)], default=0)

    def validate_repeat_interval(self, field):
        if (self.repeat_frequency.data, self.repeat_interval.data) not in RepeatMapping.mapping:
            raise ValidationError('Invalid repeat step')

    def validate_start_dt(self, field):
        if field.data != field.object_data and field.data.date() < date.today() and not session.user.is_admin:
            raise ValidationError(_('The start time cannot be in the past.'))

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
                                      choices=[(0, _('Exact')),
                                               (1, '&plusmn;{}'.format(_('1 day'))),
                                               (2, '&plusmn;{}'.format(_('2 days'))),
                                               (3, '&plusmn;{}'.format(_('3 days')))])

    def validate_flexible_dates_range(self, field):
        if self.repeat_frequency.data == RepeatFrequency.DAY:
            field.data = 0


class NewBookingPeriodForm(NewBookingFormBase):
    room_id = IntegerField('Room', [DataRequired()], widget=HiddenInput())


class NewBookingConfirmForm(NewBookingPeriodForm):
    room_usage = RadioField([DataRequired()], choices=[('current_user', _("I'll be using the room myself")),
                                                       ('other_user', _("I'm booking the room for someone else"))])
    booked_for_user = PrincipalField(_('User'), [HiddenUnless('room_usage', 'other_user'),
                                                 DataRequired()], allow_external=True)
    booking_reason = TextAreaField(_('Reason'), [DataRequired()])
    uses_vc = BooleanField(_('I will use videoconference equipment'))
    used_equipment = IndicoQuerySelectMultipleCheckboxField(_('VC equipment'), get_label=lambda x: x.name)
    needs_vc_assistance = BooleanField(_('Request assistance for the startup of the videoconference session. '
                                         'This support is usually performed remotely.'))
    needs_assistance = BooleanField(_('Request personal assistance for meeting startup'))
    submit_book = SubmitField(_('Create booking'))
    submit_prebook = SubmitField(_('Create pre-booking'))

    def validate_used_equipment(self, field):
        if field.data and not self.uses_vc.data:
            raise ValidationError(_('Videoconference equipment is not used.'))
        elif not field.data and self.uses_vc.data:
            raise ValidationError(_('Please select the type of videoconference that you will use.'))

    def validate_needs_vc_assistance(self, field):
        if field.data and not self.uses_vc.data:
            raise ValidationError(_('Videoconference equipment is not used.'))


class NewBookingSimpleForm(NewBookingConfirmForm):
    submit_check = SubmitField(_('Check conflicts'))
    booking_reason = TextAreaField(_('Reason'), [UsedIf(lambda form, field: not form.submit_check.data),
                                                 DataRequired()])
    room_usage = RadioField(validators=[UsedIf(lambda form, field: not form.submit_check.data), DataRequired()],
                            choices=[('current_user', _("I'll be using the room myself")),
                                     ('other_user', _("I'm booking the room for someone else"))])
    booked_for_user = PrincipalField(_('User'), [UsedIf(lambda form, field: not form.submit_check.data),
                                                 HiddenUnless('room_usage', 'other_user'),
                                                 DataRequired()], allow_external=True)


class ModifyBookingForm(NewBookingSimpleForm):
    submit_update = SubmitField(_('Update booking'))

    def __init__(self, *args, **kwargs):
        self._old_start_dt = kwargs.pop('old_start_dt')
        self._old_end_dt = kwargs.pop('old_end_dt')
        super(ModifyBookingForm, self).__init__(*args, **kwargs)
        if self.room_usage.data == 'None':
            self.room_usage.data = 'current_user' if self.booked_for_user.data == session.user else 'other_user'
        del self.room_id
        del self.submit_book
        del self.submit_prebook

    def validate_start_dt(self, field):
        super(ModifyBookingForm, self).validate_start_dt(field)
        new_start_dt = field.data
        now = datetime.now()

        if self._old_start_dt < now and new_start_dt != self._old_start_dt and not session.user.is_admin:
            raise ValidationError(_("The start time is in the past and cannot be modified."))
        if self._old_start_dt >= now and new_start_dt < now and not session.user.is_admin:
            raise ValidationError(_('The start time cannot be moved into the past.'))

    def validate_end_dt(self, field):
        super(ModifyBookingForm, self).validate_end_dt(field)
        new_end_dt = field.data
        now = datetime.now()

        if self._old_end_dt < now and new_end_dt != self._old_end_dt and not session.user.is_admin:
            raise ValidationError(_("The end time is in the past and cannot be modified."))
        if self._old_end_dt >= now and new_end_dt < now and not session.user.is_admin:
            raise ValidationError(_('The end time cannot be moved into the past.'))
