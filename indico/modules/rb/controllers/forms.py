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

from flask_wtf import Form
from wtforms import (
    BooleanField,
    FieldList,
    IntegerField,
    StringField,
    validators
)
from wtforms.ext.dateutil.fields import DateTimeField
from wtforms_alchemy import model_form_factory

from indico.core.errors import IndicoError

from ..models.reservations import Reservation


ModelForm = model_form_factory(Form, strip_string_fields=True)


class BookingListForm(ModelForm):

    is_only_pre_bookings = BooleanField('Only Prebookings', default=False)
    is_only_bookings = BooleanField('Only Bookings', default=False)
    is_only_mine = BooleanField('Only Mine', default=False)
    is_only_my_rooms = BooleanField('Only My Rooms', default=False)
    is_search = BooleanField('Search', default=False)
    is_new_booking = BooleanField('New Booking', default=False)
    is_auto = BooleanField('Auto', default=False)
    is_today = BooleanField('Today', default=False)
    is_archival = BooleanField('Is Archival', default=False)
    is_heavy = BooleanField('Is Heavy', default=False)

    flexible_dates_range = IntegerField('Flexible Date Range', default=0)
    finish_date = DateTimeField('Finish Date', default=False, display_format='%Y-%m-%d %H:%M:%S')

    room_id_list = FieldList(IntegerField('Room IDs'))

    class Meta:
        model = Reservation

    def __getattr__(self, attr):
        if attr == 'is_all_rooms':
            return -1 in self.room_id_list.data
        raise IndicoError('{} has no attribute: {}'.format(self.__class__.__name__, attr))
