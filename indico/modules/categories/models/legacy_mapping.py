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

from indico.core.db import db
from indico.util.string import return_ascii


class LegacyCategoryMapping(db.Model):
    """Legacy category ID mapping

    Legacy categories have non-numeric IDs which are not supported by
    any new code. This mapping maps them to proper integer IDs to
    avoid breaking things.
    """

    __tablename__ = 'legacy_id_map'
    __table_args__ = {'schema': 'categories'}

    legacy_category_id = db.Column(
        db.String,
        primary_key=True,
        index=True
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        index=True,
        primary_key=True,
        autoincrement=False
    )

    category = db.relationship(
        'Category',
        lazy=True,
        backref=db.backref(
            'legacy_mapping',
            uselist=False,
            lazy=True
        )
    )

    @return_ascii
    def __repr__(self):
        return '<LegacyCategoryMapping({}, {})>'.format(self.legacy_category_id, self.category_id)
