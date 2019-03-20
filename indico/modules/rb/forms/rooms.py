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

from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields.core import BooleanField, IntegerField, StringField
from wtforms.validators import NumberRange, Optional

from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.locations import Location
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoQuerySelectMultipleCheckboxField


class SearchRoomsForm(IndicoForm):
    location = QuerySelectField(_(u'Location'), get_label=lambda x: x.name, query_factory=Location.find,
                                allow_blank=True)
    details = StringField()
    capacity = IntegerField(_(u'Capacity'), validators=[Optional(), NumberRange(min=0)])
    available_equipment = IndicoQuerySelectMultipleCheckboxField(_(u'Equipment'), get_label=u'name',
                                                                 query_factory=lambda: EquipmentType.find().order_by(
                                                                     EquipmentType.name))
    is_only_public = BooleanField(_(u'Only public rooms'), default=True)
    is_auto_confirm = BooleanField(_(u'Only rooms not requiring confirmation'), default=True)
    is_only_active = BooleanField(_(u'Only active rooms'), default=True)
    is_only_my_rooms = BooleanField(_(u'Only my rooms'))
    repeatability = StringField()  # TODO: use repeat_frequency/interval with new UI
    include_pending_blockings = BooleanField(_(u'Check conflicts against pending blockings'), default=True)
    include_pre_bookings = BooleanField(_(u'Check conflicts against pre-bookings'), default=True)
