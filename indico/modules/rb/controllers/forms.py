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

import itertools
import json
from collections import defaultdict
from datetime import datetime, date, timedelta

from flask import session
from flask.ext.wtf import Form
from flask.ext.wtf.file import FileField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField
from wtforms.fields.core import (BooleanField, FloatField, IntegerField, StringField, FieldList, FormField, RadioField,
                                 SelectMultipleField)
from wtforms.fields.simple import HiddenField, TextAreaField, SubmitField
from wtforms.validators import (Optional, NumberRange, DataRequired, ValidationError, StopValidation,
                                InputRequired)
from wtforms.ext.dateutil.fields import DateTimeField, DateField
from wtforms.widgets import CheckboxInput, HiddenInput, HTMLString
from wtforms_components import TimeField

from indico.util.i18n import _
from indico.util.string import is_valid_mail
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import RepeatUnit, RepeatMapping
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.room_equipments import RoomEquipment
from MaKaC.user import GroupHolder, AvatarHolder


def auto_datetime(diff=None):
    return (diff if diff else timedelta(0)) + datetime.utcnow()


def auto_date(specified_time):
    return datetime.combine(auto_datetime(), specified_time)


def _get_equipment_label(eq):
    parents = []
    parent = eq.parent
    while parent:
        parents.append(parent.name)
        parent = parent.parent
    return ': '.join(itertools.chain(reversed(parents), [eq.name]))


def _group_equipment(objects, _tree=None, _child_of=None):
    """Groups the equipment list so children follow their their parents"""
    if _tree is None:
        _tree = defaultdict(list)
        for obj in objects:
            _tree[obj[1].parent_id].append(obj)

    for obj in _tree[_child_of]:
        yield obj
        for child in _group_equipment(objects, _tree, obj[1].id):
            yield child


class DataWrapper(object):
    """Wrapper for the return value of generated_data properties"""
    def __init__(self, data):
        self.data = data


class IndicoForm(Form):
    __generated_data__ = ()

    def populate_obj(self, obj, fields=None, skip=None, existing_only=False):
        """Populates the given object with form data.

        If `fields` is set, only fields from that list are populated.
        If `skip` is set, fields in that list are skipped.
        If `existing_only` is True, only attributes that already exist on `obj` are populated.
        """
        for name, field in self._fields.iteritems():
            if fields and name not in fields:
                continue
            if skip and name in skip:
                continue
            if existing_only and not hasattr(obj, name):
                continue
            field.populate_obj(obj, name)

    @property
    def error_list(self):
        all_errors = []
        for field_name, errors in self.errors.iteritems():
            for error in errors:
                if isinstance(error, dict) and isinstance(self[field_name], FieldList):
                    for field in self[field_name].entries:
                        all_errors += ['{}: {}'.format(self[field_name].label.text, sub_error)
                                       for sub_error in field.form.error_list]
                else:
                    all_errors.append('{}: {}'.format(self[field_name].label.text, error))
        return all_errors

    @property
    def data(self):
        """Extends form.data with generated data from properties"""
        data = super(IndicoForm, self).data
        for key in self.__generated_data__:
            data[key] = getattr(self, key).data
        return data


class ConcatWidget(object):
    """Renders a list of fields as a simple string joined by an optional separator."""
    def __init__(self, separator='', prefix_label=True):
        self.separator = separator
        self.prefix_label = prefix_label

    def __call__(self, field, label_args=None, field_args=None):
        label_args = label_args or {}
        field_args = field_args or {}
        html = []
        for subfield in field:
            fmt = '{0} {1}' if self.prefix_label else '{1} {0}'
            html.append(fmt.format(subfield.label(**label_args), subfield(**field_args)))
        return HTMLString(self.separator.join(html))


class UsedIf(object):
    """Makes a WTF field "used" if a given condition evaluates to True.

    If the field is not used, validation stops.
    """
    def __init__(self, condition):
        self.condition = condition

    def __call__(self, form, field):
        if self.condition in {True, False}:
            if not self.condition:
                field.errors[:] = []
                raise StopValidation()
        elif not self.condition(form, field):
            field.errors[:] = []
            raise StopValidation()


class IndicoEmail(object):
    """Validates one or more email addresses"""
    def __init__(self, multi=False):
        self.multi = multi

    def __call__(self, form, field):
        if field.data and not is_valid_mail(field.data, self.multi):
            msg = _('Invalid email address list') if self.multi else _('Invalid email address')
            raise ValidationError(msg)


class IndicoQuerySelectMultipleField(QuerySelectMultipleField):
    """Like the parent, but with a callback that allows you to modify the list

    The callback can return a new list or yield items, and you can use it e.g. to sort the list.
    """
    def __init__(self, *args, **kwargs):
        self.modify_object_list = kwargs.pop('modify_object_list', None)
        super(IndicoQuerySelectMultipleField, self).__init__(*args, **kwargs)

    def _get_object_list(self):
        object_list = super(IndicoQuerySelectMultipleField, self)._get_object_list()
        if self.modify_object_list:
            object_list = list(self.modify_object_list(object_list))
        return object_list


class IndicoQuerySelectMultipleCheckboxField(IndicoQuerySelectMultipleField):
    option_widget = CheckboxInput()


class JSONField(HiddenField):
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = json.loads(valuelist[0])

    def _value(self):
        return json.dumps(self.data)

    def populate_obj(self, obj, name):
        # We don't want to populate an object with this
        pass


class FormDefaults(object):
    """Simple wrapper to be used for Form(obj=...) default values.

    It allows you to specify default values via kwargs or certain attrs from an object.
    You can also set attributes directly on this object, which will act just like kwargs
    """

    def __init__(self, obj=None, attrs=None, skip_attrs=None, **defaults):
        self.__obj = obj
        self.__use_items = hasattr(obj, 'iteritems') and hasattr(obj, 'get')  # smells like a dict
        self.__obj_attrs = attrs
        self.__obj_attrs_skip = skip_attrs
        self.__defaults = defaults

    def __valid_attr(self, name):
        """Checks if an attr may be retrieved from the object"""
        if self.__obj is None:
            return False
        if self.__obj_attrs is not None and name not in self.__obj_attrs:
            return False
        if self.__obj_attrs_skip is not None and name in self.__obj_attrs_skip:
            return False
        return True

    def __setitem__(self, key, value):
        self.__defaults[key] = value

    def __setattr__(self, key, value):
        if key.startswith('_{}__'.format(type(self).__name__)):
            object.__setattr__(self, key, value)
        else:
            self.__defaults[key] = value

    def __getattr__(self, item):
        if self.__valid_attr(item):
            if self.__use_items:
                return self.__obj.get(item, self.__defaults.get(item))
            else:
                return getattr(self.__obj, item, self.__defaults.get(item))
        elif item in self.__defaults:
            return self.__defaults[item]
        else:
            raise AttributeError(item)


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


class SearchRoomsForm(IndicoForm):
    location = QuerySelectField(_('Location'), get_label=lambda x: x.name, query_factory=Location.find)
    details = StringField()
    available = RadioField(_('Availability'), coerce=int, default=-1, widget=ConcatWidget(prefix_label=False),
                           choices=[(1, _('Available')), (0, _('Booked')), (-1, _("Don't care"))])
    capacity = IntegerField(_('Capacity'), validators=[NumberRange(min=0)], default=0)
    equipments = IndicoQuerySelectMultipleCheckboxField(_('Equipment'), get_label=_get_equipment_label,
                                                        modify_object_list=_group_equipment,
                                                        query_factory=lambda: RoomEquipment.find().order_by(
                                                            RoomEquipment.name))
    is_only_public = BooleanField(_('Only public rooms'), default=True)
    is_auto_confirm = BooleanField(_('Only rooms not requiring confirmation'), default=True)
    is_only_active = BooleanField(_('Only active rooms'), default=True)
    is_only_my_rooms = BooleanField(_('Only my rooms'))
    # Period details when searching for (un-)availability
    start_date = DateTimeField(_('Start date'), validators=[Optional()], parse_kwargs={'dayfirst': True},
                               display_format='%d/%m/%Y %H:%M', widget=HiddenInput())
    end_date = DateTimeField(_('End date'), validators=[Optional()], parse_kwargs={'dayfirst': True},
                             display_format='%d/%m/%Y %H:%M', widget=HiddenInput())
    repeatability = StringField()  # TODO: use repeat_unit/step with new UI
    include_pending_blockings = BooleanField(_('Check conflicts against pending blockings'), default=True)
    include_pre_bookings = BooleanField(_('Check conflicts against pre-bookings'), default=True)


class BlockingForm(IndicoForm):
    reason = TextAreaField(_('Reason'), [DataRequired()])
    principals = JSONField(default=[])
    blocked_rooms = JSONField(default=[])

    def validate_blocked_rooms(self, field):
        try:
            field.data = map(int, field.data)
        except Exception as e:
            # In case someone sent crappy data
            raise ValidationError(str(e))

        # Make sure all room ids are valid
        if len(field.data) != Room.find(Room.id.in_(field.data)).count():
            raise ValidationError('Invalid rooms')

        if hasattr(self, '_blocking'):
            start_date = self._blocking.start_date
            end_date = self._blocking.end_date
            blocking_id = self._blocking.id
        else:
            start_date = self.start_date.data
            end_date = self.end_date.data
            blocking_id = None

        overlap = BlockedRoom.find_first(
            BlockedRoom.room_id.in_(field.data),
            BlockedRoom.state != BlockedRoom.State.rejected,
            Blocking.start_date <= end_date,
            Blocking.end_date >= start_date,
            Blocking.id != blocking_id,
            _join=Blocking
        )
        if overlap:
            msg = 'Your blocking for {} is overlapping with another blocking.'.format(overlap.room.getFullName())
            raise ValidationError(msg)

    def validate_principals(self, field):
        for item in field.data:
            try:
                type_ = item['_type']
                id_ = item['id']
            except Exception as e:
                raise ValidationError('Invalid principal data: {}'.format(e))
            if type_ not in ('Avatar', 'Group', 'LDAPGroup'):
                raise ValidationError('Invalid principal data: type={}'.format(type_))
            holder = AvatarHolder() if type_ == 'Avatar' else GroupHolder()
            if not holder.getById(id_):
                raise ValidationError('Invalid principal: {}:{}'.format(type_, id_))


class CreateBlockingForm(BlockingForm):
    start_date = DateField(_('Start date'), [DataRequired()], parse_kwargs={'dayfirst': True})
    end_date = DateField(_('End date'), [DataRequired()], parse_kwargs={'dayfirst': True})

    def validate_start_date(self, field):
        if self.start_date.data > self.end_date.data:
            raise ValidationError('Blocking may not end before it starts!')

    validate_end_date = validate_start_date


class _TimePair(IndicoForm):
    start = TimeField(_('from'), [UsedIf(lambda form, field: form.end.data)])
    end = TimeField(_('to'), [UsedIf(lambda form, field: form.start.data)])

    def validate_start(self, field):
        if self.start.data and self.end.data and self.start.data >= self.end.data:
            raise ValidationError('The start time must be earlier than the end time.')

    validate_end = validate_start


class _DateTimePair(IndicoForm):
    start = DateTimeField(_('from'), [UsedIf(lambda form, field: form.end.data)], display_format='%d/%m/%Y %H:%M')
    end = DateTimeField(_('to'), [UsedIf(lambda form, field: form.start.data)], display_format='%d/%m/%Y %H:%M')

    def validate_start(self, field):
        if self.start.data and self.end.data and self.start.data >= self.end.data:
            raise ValidationError('The start date must be earlier than the end date.')

    validate_end = validate_start


class RoomForm(IndicoForm):
    name = StringField(_('Name'))
    site = StringField(_('Site'))
    building = StringField(_('Building'), [DataRequired()])
    floor = StringField(_('Floor'), [DataRequired()])
    number = StringField(_('Number'), [DataRequired()])
    longitude = FloatField(_('Longitude'), [Optional(), NumberRange(min=0)])
    latitude = FloatField(_('Latitude'), [Optional(), NumberRange(min=0)])
    is_active = BooleanField(_('Active'))
    is_reservable = BooleanField(_('Public'))
    reservations_need_confirmation = BooleanField(_('Confirmations'))
    notification_for_assistance = BooleanField(_('Assistance'))
    notification_for_start = IntegerField(_('Notification on booking start - X days before'),
                                          [Optional(), NumberRange(min=0, max=9)])
    notification_for_end = BooleanField(_('Notification on booking end'))
    notification_for_responsible = BooleanField(_('Notification to responsible, too'))
    owner_id = HiddenField(_('Responsible user'), [DataRequired()])
    key_location = StringField(_('Where is key?'))
    telephone = StringField(_('Telephone'))
    capacity = IntegerField(_('Capacity'), [DataRequired(), NumberRange(min=1)])
    division = StringField(_('Department'))
    surface_area = IntegerField(_('Surface area'), [NumberRange(min=0)])
    max_advance_days = IntegerField(_('Maximum advance time for bookings'), [NumberRange(min=1)])
    comments = TextAreaField(_('Comments'))
    delete_photos = BooleanField(_('Delete photos'))
    large_photo = FileField(_('Large photo'))
    small_photo = FileField(_('Small photo'))
    equipments = IndicoQuerySelectMultipleCheckboxField(_('Equipment'), get_label=_get_equipment_label,
                                                        modify_object_list=_group_equipment)
    # attribute_* - set at runtime
    bookable_times = FieldList(FormField(_TimePair), min_entries=1)
    nonbookable_dates = FieldList(FormField(_DateTimePair), min_entries=1)

    def validate_large_photo(self, field):
        if not field.data and self.small_photo.data:
            raise ValidationError(_('When uploading a small photo you need to upload a large photo, too.'))

    def validate_small_photo(self, field):
        if not field.data and self.large_photo.data:
            raise ValidationError(_('When uploading a large photo you need to upload a small photo, too.'))
