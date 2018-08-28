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

from marshmallow.fields import Method

from indico.core.marshmallow import mm
from indico.modules.users import User


class UserSchema(mm.ModelSchema):
    identifier = Method('get_identifier')

    class Meta:
        model = User
        fields = ('id', 'identifier', 'first_name', 'last_name', 'email', 'affiliation', 'avatar_bg_color', 'full_name')

    def get_identifier(self, user):
        return 'User:{}'.format(user.id)


user_schema = UserSchema()
