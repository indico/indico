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

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


class RoomFeature(db.Model):
    __tablename__ = 'features'
    __table_args__ = (db.CheckConstraint("icon != '' OR NOT show_filter_button", 'icon_if_filter_button'),
                      {'schema': 'roombooking'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False,
        index=True,
        unique=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    icon = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    show_filter_button = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # relationship backrefs:
    # - equipment_types (EquipmentType.features)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'name', _text=self.title)
