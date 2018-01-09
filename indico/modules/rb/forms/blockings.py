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


from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, ValidationError

from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.rooms import Room
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoDateField, JSONField, PrincipalListField


class BlockingForm(IndicoForm):
    reason = TextAreaField(_(u'Reason'), [DataRequired()])
    principals = PrincipalListField(groups=True, allow_external=True)
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
            msg = 'Your blocking for {} is overlapping with another blocking.'.format(overlap.room.full_name)
            raise ValidationError(msg)


class CreateBlockingForm(BlockingForm):
    start_date = IndicoDateField(_(u'Start date'), [DataRequired()])
    end_date = IndicoDateField(_(u'End date'), [DataRequired()])

    def validate_start_date(self, field):
        if self.start_date.data > self.end_date.data:
            raise ValidationError('Blocking may not end before it starts!')

    validate_end_date = validate_start_date
