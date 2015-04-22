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

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.util.string import return_ascii


class LocalGroup(db.Model):
    __tablename__ = 'groups'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_groups_name_lower', db.func.lower(cls.name), unique=True),
                {'schema': 'users'})

    #: the unique id of the group
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: the name of the group
    name = db.Column(
        db.String,
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - members (User.local_groups)

    @property
    def as_legacy_group(self):
        # TODO: remove this after DB is free of Groups
        from indico.modules.users.legacy import LocalGroupWrapper
        return LocalGroupWrapper(self.id)

    @return_ascii
    def __repr__(self):
        return '<LocalGroup({}, {})>'.format(self.id, self.name)


group_members_table = db.Table(
    'group_members',
    db.metadata,
    db.Column(
        'group_id',
        db.Integer,
        db.ForeignKey('users.groups.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    schema='users'
)
