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
from datetime import datetime, time, timedelta
from functools import partial

from flask.ext.wtf import Form
from flask.ext.wtf.file import FileField
from wtforms import BooleanField, Field, IntegerField, SelectField, StringField, validators, HiddenField, TextAreaField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.fields.core import FloatField, FieldList, FormField
from wtforms.validators import any_of, optional, number_range, required
from wtforms.ext.dateutil.fields import DateTimeField, DateField
from wtforms.widgets import CheckboxInput
from wtforms_alchemy import model_form_factory
from wtforms_components import TimeField

from indico.core.errors import IndicoError
from indico.util.i18n import _
from indico.util.string import is_valid_mail
from indico.modules.rb.models.reservations import Reservation, RepeatUnit, RepeatMapping
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.rooms import Room
from MaKaC.user import GroupHolder, AvatarHolder


ModelForm = model_form_factory(Form, strip_string_fields=True)

AVAILABILITY_VALUES = ['Available', 'Booked', "Don't care"]


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


class IndicoForm(Form):
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
                raise validators.StopValidation()
        elif not self.condition(form, field):
            field.errors[:] = []
            raise validators.StopValidation()


class EmailList(object):
    def __init__(self, multi=True):
        self.multi = multi

    def __call__(self, form, field):
        if field.data and not is_valid_mail(field.data, self.multi):
            msg = _('Invalid email address list') if self.multi else _('Invalid email address')
            raise validators.ValidationError(msg)


class IndicoQuerySelectMultipleField(QuerySelectMultipleField):
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
        if raw_data:
            try:
                self.data = datetime.combine(datetime(*map(int, raw_data[:-1])),
                                             datetime.strptime(raw_data[-1], '%H:%M'))
            except:
                self.data = datetime(*map(int, raw_data))

    def _process(self, formdata, data=None):
        if formdata:
            try:
                try:
                    self.raw_data = [formdata.getlist(p)[0] for p in self.parameter_name if formdata.getlist(p)]
                except KeyError:
                    camel_name = self.underscore_to_camel_case(self.name) in formdata
                    if camel_name in formdata:
                        self.raw_data = formdata.getlist(self.name)
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


class JSONField(HiddenField):
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = json.loads(valuelist[0])

    def _value(self):
        return json.dumps(self.data)

    def populate_obj(self, obj, name):
        pass


class FormDefaults(object):
    """Simple wrapper to be used for Form(obj=...) default values.

    It allows you to specify default values via kwargs or certain attrs from an object.
    You can also set attributes directly on this object, which will act just like kwargs
    """

    def __init__(self, obj=None, attrs=None, skip_attrs=None, **defaults):
        self.__obj = obj
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
            return getattr(self.__obj, item, self.__defaults.get(item))
        elif item in self.__defaults:
            return self.__defaults[item]
        else:
            raise AttributeError(item)


class BookingListForm(Form):
    is_only_pre_bookings = BooleanField('Only Prebookings', [validators.Optional()], default=False)
    is_only_bookings = BooleanField('Only Bookings', [validators.Optional()], default=False)
    is_only_mine = BooleanField('Only Mine', [validators.Optional()], default=False)
    is_only_my_rooms = BooleanField('Only My Rooms', [validators.Optional()], default=False)
    is_search = BooleanField('Search', [validators.Optional()], default=True)
    is_new_booking = BooleanField('New Booking', [validators.Optional()], default=False)
    is_auto = BooleanField('Auto', [validators.Optional()], default=False)
    is_today = BooleanField('Today', [validators.Optional()], default=False)
    is_archival = BooleanField('Is Archival', [validators.Optional()], default=False)

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
                                          parameter_name='is_only_mine')
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


class BlockingForm(IndicoForm):
    reason = TextAreaField(_('Reason'), [validators.DataRequired()])
    principals = JSONField(default=[])
    blocked_rooms = JSONField(default=[])

    def validate_blocked_rooms(self, field):
        try:
            field.data = map(int, field.data)
        except Exception as e:
            # In case someone sent crappy data
            raise validators.ValidationError(str(e))

        # Make sure all room ids are valid
        if len(field.data) != Room.find(Room.id.in_(field.data)).count():
            raise validators.ValidationError('Invalid rooms')

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
            raise validators.ValidationError(msg)

    def validate_principals(self, field):
        for item in field.data:
            try:
                type_ = item['_type']
                id_ = item['id']
            except Exception as e:
                raise validators.ValidationError('Invalid principal data: {}'.format(e))
            if type_ not in ('Avatar', 'Group', 'LDAPGroup'):
                raise validators.ValidationError('Invalid principal data: type={}'.format(type_))
            holder = AvatarHolder() if type_ == 'Avatar' else GroupHolder()
            if not holder.getById(id_):
                raise validators.ValidationError('Invalid principal: {}:{}'.format(type_, id_))


class CreateBlockingForm(BlockingForm):
    start_date = DateField(_('Start date'), [validators.DataRequired()])
    end_date = DateField(_('End date'), [validators.DataRequired()])

    def validate_start_date(self, field):
        if self.start_date.data > self.end_date.data:
            raise validators.ValidationError('Blocking may not end before it starts!')

    validate_end_date = validate_start_date


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


class _TimePair(IndicoForm):
    start = TimeField(_('from'), [UsedIf(lambda form, field: form.end.data)])
    end = TimeField(_('to'), [UsedIf(lambda form, field: form.start.data)])

    def validate_start(self, field):
        if self.start.data and self.end.data and self.start.data >= self.end.data:
            raise validators.ValidationError('The start time must be earlier than the end time.')

    validate_end = validate_start


class _DateTimePair(IndicoForm):
    start = DateTimeField(_('from'), [UsedIf(lambda form, field: form.end.data)], display_format='%d/%m/%Y %H:%M')
    end = DateTimeField(_('to'), [UsedIf(lambda form, field: form.start.data)], display_format='%d/%m/%Y %H:%M')

    def validate_start(self, field):
        if self.start.data and self.end.data and self.start.data >= self.end.data:
            raise validators.ValidationError('The start date must be earlier than the end date.')

    validate_end = validate_start


class RoomForm(IndicoForm):
    name = StringField(_('Name'))
    site = StringField(_('Site'))
    building = StringField(_('Building'), [validators.DataRequired()])
    floor = StringField(_('Floor'), [validators.DataRequired()])
    number = StringField(_('Number'), [validators.DataRequired()])
    longitude = FloatField(_('Longitude'), [validators.Optional(), validators.NumberRange(min=0)])
    latitude = FloatField(_('Latitude'), [validators.Optional(), validators.NumberRange(min=0)])
    is_active = BooleanField(_('Active'))
    is_reservable = BooleanField(_('Public'))
    reservations_need_confirmation = BooleanField(_('Confirmations'))
    notification_for_assistance = BooleanField(_('Assistance'))
    notification_for_start = IntegerField(_('Notification on booking start - X days before'),
                                          [validators.Optional(), validators.NumberRange(min=0, max=9)])
    notification_for_end = BooleanField(_('Notification on booking end'))
    notification_for_responsible = BooleanField(_('Notification to responsible, too'))
    owner_id = HiddenField(_('Responsible user'), [validators.DataRequired()])
    key_location = StringField(_('Where is key?'))
    telephone = StringField(_('Telephone'))
    capacity = IntegerField(_('Capacity'), [validators.DataRequired(), validators.NumberRange(min=1)])
    division = StringField(_('Department'))
    surface_area = IntegerField(_('Surface area'), [validators.NumberRange(min=0)])
    max_advance_days = IntegerField(_('Maximum advance time for bookings'), [validators.NumberRange(min=1)])
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
            raise validators.ValidationError(_('When uploading a small photo you need to upload a large photo, too.'))

    def validate_small_photo(self, field):
        if not field.data and self.large_photo.data:
            raise validators.ValidationError(_('When uploading a large photo you need to upload a small photo, too.'))
