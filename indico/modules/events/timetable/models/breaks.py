# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.core.db.sqlalchemy.util.models import auto_table_args
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorMixin
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.util.string import format_repr, return_ascii


class Break(ColorMixin, LocationMixin, db.Model):
    __tablename__ = 'breaks'
    __auto_table_args = {'schema': 'events'}
    location_backref_name = 'breaks'

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    duration = db.Column(
        db.Interval,
        nullable=False
    )

    # relationship backrefs:
    # - timetable_entry (TimetableEntry.break_)

    @property
    def location_parent(self):
        return (self.timetable_entry.event_new
                if self.timetable_entry.parent_id is None
                else self.timetable_entry.parent.session_block)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.title)
