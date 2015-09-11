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

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import joinedload

from indico.core.db.sqlalchemy import db, PyIntEnum
from indico.core.roles import get_available_roles
from indico.util.decorators import strict_classproperty, classproperty
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
    #: The columns which should be included in the unique constraints.
    #: If set to ``None``, no unique constraints will be added.
    unique_columns = None

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        uniques = ()
        if cls.unique_columns:
            uniques = (db.Index('ix_uq_{}_user'.format(cls.__tablename__), 'user_id', *cls.unique_columns, unique=True,
                                postgresql_where=db.text('type = {}'.format(PrincipalType.user))),
                       db.Index('ix_uq_{}_local_group'.format(cls.__tablename__), 'local_group_id', *cls.unique_columns,
                                unique=True, postgresql_where=db.text('type = {}'.format(PrincipalType.local_group))),
                       db.Index('ix_uq_{}_mp_group'.format(cls.__tablename__), 'mp_group_provider', 'mp_group_name',
                                *cls.unique_columns, unique=True,
                                postgresql_where=db.text('type = {}'.format(PrincipalType.multipass_group))))
        return (db.Index(None, 'mp_group_provider', 'mp_group_name'),
                _make_check(PrincipalType.user, 'user_id'),
                _make_check(PrincipalType.local_group, 'local_group_id'),
                _make_check(PrincipalType.multipass_group, 'mp_group_provider', 'mp_group_name')) + uniques

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

    @classmethod
    def merge_users(cls, target, source, relationship_attr):
        """Merges two users in the ACL.

        :param target: The target user of the merge.
        :param source: The user that is being merged into `target`.
        :param relationship_attr: The name of the relationship pointing
                                  to the object associated with the ACL
                                  entry.
        """
        relationship = getattr(cls, relationship_attr)
        source_principals = set(getattr(source, cls.principal_backref_name).options(joinedload(relationship)))
        target_objects = {getattr(x, relationship_attr)
                          for x in getattr(target, cls.principal_backref_name).options(joinedload(relationship))}
        for principal in source_principals:
            if getattr(principal, relationship_attr) not in target_objects:
                principal.user_id = target.id
            else:
                db.session.delete(principal)
        db.session.flush()


class PrincipalRolesMixin(PrincipalMixin):
    #: The model for which we are a principal.  May also be a string
    #: containing the model's class name.
    principal_for = None

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        return db.CheckConstraint('read_access OR full_access OR array_length(roles, 1) IS NOT NULL', 'has_privs'),

    read_access = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    full_access = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    roles = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )

    @classproperty
    @classmethod
    def principal_for_obj(cls):
        if isinstance(cls.principal_for, basestring):
            return db.Model._decl_class_registry[cls.principal_for]
        else:
            return cls.principal_for

    @hybrid_method
    def has_management_role(self, role=None, explicit=False):
        """Checks whether a principal has a certain management role.

        The check always succeeds if the user is a full manager; in
        that case the list of roles is ignored.

        :param role: The role to check for or 'ANY' to check for any
                     management role.
        :param explicit: Whether to check for the role itself even if
                         the user has full management privileges.
        """
        if role is None:
            if explicit:
                raise ValueError('role must be specified if explicit=True')
            return self.full_access
        elif not explicit and self.full_access:
            return True
        valid_roles = get_available_roles(self.principal_for_obj).viewkeys()
        current_roles = set(self.roles) & valid_roles
        if role == 'ANY':
            return bool(current_roles)
        assert role in valid_roles, "invalid role '{}' for object '{}'".format(role, self.principal_for_obj)
        return role in current_roles

    @has_management_role.expression
    def has_management_role(cls, role=None, explicit=False):
        if role is None:
            if explicit:
                raise ValueError('role must be specified if explicit=True')
            return cls.full_access
        valid_roles = get_available_roles(cls.principal_for_obj).viewkeys()
        if role == 'ANY':
            crit = (cls.roles.op('&&')(db.func.cast(valid_roles, ARRAY(db.String))))
        else:
            assert role in valid_roles, "invalid role '{}' for object '{}'".format(role, cls.principal_for_obj)
            crit = (cls.roles.op('&&')(db.func.cast([role], ARRAY(db.String))))
        if explicit:
            return crit
        else:
            return cls.full_access | crit
