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

import itertools
from collections import defaultdict

from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.ext.dateutil.fields import DateTimeField
from wtforms.fields.core import StringField, RadioField, IntegerField, BooleanField, FloatField, FieldList, FormField
from wtforms.validators import NumberRange, Optional, DataRequired, ValidationError
from wtforms.widgets.core import HiddenInput
from wtforms.fields.simple import HiddenField, TextAreaField, FileField
from wtforms_components import TimeField

from indico.modules.rb.forms.base import IndicoForm
from indico.modules.rb.forms.fields import IndicoQuerySelectMultipleCheckboxField
from indico.modules.rb.forms.validators import UsedIf
from indico.modules.rb.forms.widgets import ConcatWidget
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.room_equipments import RoomEquipment
from indico.util.i18n import _


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


class SearchRoomsForm(IndicoForm):
    location = QuerySelectField(_('Location'), get_label=lambda x: x.name, query_factory=Location.find)
    details = StringField()
    available = RadioField(_('Availability'), coerce=int, default=-1, widget=ConcatWidget(prefix_label=False),
                           choices=[(1, _('Available')), (0, _('Booked')), (-1, _("Don't care"))])
    capacity = IntegerField(_('Capacity'), validators=[Optional(), NumberRange(min=0)])
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
