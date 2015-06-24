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

from indico.core.db.sqlalchemy import db, PyIntEnum
from indico.util.decorators import strict_classproperty
from indico.util.struct.enum import IndicoEnum


class PrincipalType(int, IndicoEnum):
    user = 1
    local_group = 2
    multipass_group = 3


def _make_check(type_, *cols):
    all_cols = {'user_id', 'local_group_id', 'mp_group_provider', 'mp_group_name'}
    required_cols = all_cols & set(cols)
    forbidden_cols = all_cols - required_cols
    criteria = ['{} IS NULL'.format(col) for col in forbidden_cols]
    criteria += ['{} IS NOT NULL'.format(col) for col in required_cols]
    condition = 'type != {} OR ({})'.format(type_, ' AND '.join(criteria))
    return db.CheckConstraint(condition, 'valid_{}'.format(type_.name))


class PrincipalMixin(object):
    #: The name of the backref added to `User` and `LocalGroup`.
    #: For consistency, it is recommended to name the backref
    #: ``in_foo_acl`` with *foo* describing the ACL where this
    #: mixin is used.
    principal_backref_name = None

    @strict_classproperty
    @staticmethod
    def __auto_table_args():
        return (db.Index(None, 'mp_group_provider', 'mp_group_name'),
                _make_check(PrincipalType.user, 'user_id'),
                _make_check(PrincipalType.local_group, 'local_group_id'),
                _make_check(PrincipalType.multipass_group, 'mp_group_provider', 'mp_group_name'))

    type = db.Column(
        PyIntEnum(PrincipalType)
    )
    multipass_group_provider = db.Column(
        'mp_group_provider',  # otherwise the index name doesn't fit in 60 chars
        db.String,
        nullable=True
    )
    multipass_group_name = db.Column(
        'mp_group_name',  # otherwise the index name doesn't fit in 60 chars
        db.String,
        nullable=True
    )

    @declared_attr
    def user_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('users.users.id'),
            nullable=True,
            index=True
        )

    @declared_attr
    def local_group_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('users.groups.id'),
            nullable=True,
            index=True
        )

    @declared_attr
    def user(cls):
        assert cls.principal_backref_name
        return db.relationship(
            'User',
            lazy=False,
            backref=db.backref(
                cls.principal_backref_name,
                cascade='all, delete-orphan',
                lazy='dynamic'
            )
        )

    @declared_attr
    def local_group(cls):
        assert cls.principal_backref_name
        return db.relationship(
            'LocalGroup',
            lazy=False,
            backref=db.backref(
                cls.principal_backref_name,
                cascade='all, delete-orphan',
                lazy='dynamic'
            )
        )

    @property
    def principal(self):
        from indico.modules.groups import GroupProxy
        if self.type == PrincipalType.user:
            return self.user
        elif self.type == PrincipalType.local_group:
            return self.local_group.proxy
        elif self.type == PrincipalType.multipass_group:
            return GroupProxy(self.multipass_group_name, self.multipass_group_provider)

    @principal.setter
    def principal(self, value):
        self.user = None
        self.local_group = None
        self.multipass_group_provider = self.multipass_group_name = None
        if value.is_group:
            if value.is_local:
                self.type = PrincipalType.local_group
                self.local_group = value.group
            else:
                self.type = PrincipalType.multipass_group
                self.multipass_group_provider = value.provider
                self.multipass_group_name = value.name
        else:
            self.type = PrincipalType.user
            self.user = value
