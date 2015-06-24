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

from indico.core.db import db
from indico.util.string import return_ascii

favorite_user_table = db.Table(
    'favorite_users',
    db.metadata,
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    db.Column(
        'target_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        nullable=False
    ),
    schema='users'
)


# TODO: change this to a proper many-to-many association once categories are in SQL
class FavoriteCategory(db.Model):
    __tablename__ = 'favorite_categories'
    __table_args__ = {'schema': 'users'}

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        nullable=False,
        index=True
    )
    target_id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False,
        autoincrement=False
    )

    @property
    def target(self):
        from MaKaC.conference import CategoryManager
        return CategoryManager().getById(self.target_id, True)

    @target.setter
    def target(self, value):
        self.target_id = value.id

    @return_ascii
    def __repr__(self):
        return '<FavoriteCategory({}, {})>'.format(self.user_id, self.target_id)
