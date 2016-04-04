# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorMixin, ColorTuple
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.util.string import format_repr, return_ascii


class Break(DescriptionMixin, ColorMixin, LocationMixin, db.Model):
    __tablename__ = 'breaks'
    __auto_table_args = {'schema': 'events'}
    location_backref_name = 'breaks'
    default_colors = ColorTuple('#202020', '#90c0f0')

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


Break.register_location_events()


@listens_for(Break.duration, 'set')
def _set_duration(target, value, oldvalue, *unused):
    from indico.modules.events.util import register_time_change
    if oldvalue is not None and value != oldvalue and target.timetable_entry is not None:
        register_time_change(target.timetable_entry)
