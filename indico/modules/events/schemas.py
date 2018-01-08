# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from marshmallow_enum import EnumField

from indico.core.marshmallow import mm
from indico.modules.events.contributions.models.persons import AuthorType


class PersonLinkSchema(mm.Schema):
    author_type = EnumField(AuthorType)

    class Meta:
        additional = ('id', 'person_id', 'email', 'first_name', 'last_name', 'title', 'affiliation', 'address',
                      'phone', 'is_speaker')
