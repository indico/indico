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

from indico.core.db import db
from indico.util.string import return_ascii


class Holiday(db.Model):
    __tablename__ = 'holidays'
    __table_args__ = (db.UniqueConstraint('date', 'location_id'),
                      {'schema': 'roombooking'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    date = db.Column(
        db.Date,
        nullable=False,
        index=True
    )
    name = db.Column(
        db.String
    )
    location_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.locations.id'),
        nullable=False
    )

    # relationship backrefs:
    # - location (Location.holidays)

    @return_ascii
    def __repr__(self):
        return u'<Holiday({}, {}, {}, {})>'.format(self.id, self.date, self.name or 'n/a', self.location.name)
