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

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property, Comparator
from sqlalchemy.orm import joinedload, noload

from indico.core.db.sqlalchemy import db, PyIntEnum
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.core.roles import get_available_roles
from indico.util.decorators import strict_classproperty, classproperty
from indico.util.fossilize import fossilizes, Fossilizable, IFossil
from indico.util.string import return_ascii, format_repr
from indico.util.struct.enum import IndicoEnum


class PrincipalType(int, IndicoEnum):
    user = 1
    local_group = 2
    multipass_group = 3
    email = 4
    network = 5


def _make_check(type_, allow_emails, allow_networks, *cols):
    all_cols = {'user_id', 'local_group_id', 'mp_group_provider', 'mp_group_name'}
    if allow_emails:
        all_cols.add('email')
    if allow_networks:
        all_cols.add('ip_network_group_id')
    required_cols = all_cols & set(cols)
    forbidden_cols = all_cols - required_cols
    criteria = ['{} IS NULL'.format(col) for col in sorted(forbidden_cols)]
    criteria += ['{} IS NOT NULL'.format(col) for col in sorted(required_cols)]
    condition = 'type != {} OR ({})'.format(type_, ' AND '.join(criteria))
    return db.CheckConstraint(condition, 'valid_{}'.format(type_.name))


class IEmailPrincipalFossil(IFossil):
    def getId(self):
        pass
    getId.produce = lambda x: x.email

    def getIdentifier(self):
        pass
    getIdentifier.produce = lambda x: 'Email:{}'.format(x.email)

    def getEmail(self):
        pass
    getEmail.produce = lambda x: x.email


class EmailPrincipal(Fossilizable):
    """Wrapper for email principals

    :param email: The email address.
    """

    principal_type = PrincipalType.email
    is_group = False
    fossilizes(IEmailPrincipalFossil)

    def __init__(self, email):
        self.email = email.lower()

    @property
    def name(self):
        return self.email

    @property
    def as_legacy(self):
        return self

    @property
    def as_new(self):
        return self

    @property
    def user(self):
        from indico.modules.users import User
        return User.find_first(~User.is_deleted, User.all_emails.contains(self.email))

    def __eq__(self, other):
        return isinstance(other, EmailPrincipal) and self.email == other.email

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.email)

    def __contains__(self, user):
        return self.email in user.all_emails

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'email')


class PrincipalMixin(object):
    #: The name of the backref added to `User` and `LocalGroup`.
    #: For consistency, it is recommended to name the backref
    #: ``in_foo_acl`` with *foo* describing the ACL where this
    #: mixin is used.
    principal_backref_name = None
    #: The columns which should be included in the unique constraints.
    #: If set to ``None``, no unique constraints will be added.
    unique_columns = None
    #: Whether it should be allowed to add a user by email address.
    #: This is useful in places where no Indico user exists yet.
    #: Usually adding an email address to an ACL should result in
    #: an email being sent to the user, inviting him to create an
    #: account with that email address.
    allow_emails = False
    #: Whether it should be allowed to add an IP network.
    allow_networks = False

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        uniques = ()
        if cls.unique_columns:
            uniques = [db.Index('ix_uq_{}_user'.format(cls.__tablename__), 'user_id', *cls.unique_columns, unique=True,
                                postgresql_where=db.text('type = {}'.format(PrincipalType.user))),
                       db.Index('ix_uq_{}_local_group'.format(cls.__tablename__), 'local_group_id', *cls.unique_columns,
                                unique=True, postgresql_where=db.text('type = {}'.format(PrincipalType.local_group))),
                       db.Index('ix_uq_{}_mp_group'.format(cls.__tablename__), 'mp_group_provider', 'mp_group_name',
                                *cls.unique_columns, unique=True,
                                postgresql_where=db.text('type = {}'.format(PrincipalType.multipass_group)))]
            if cls.allow_emails:
                uniques.append(db.Index('ix_uq_{}_email'.format(cls.__tablename__), 'email', *cls.unique_columns,
                                        unique=True, postgresql_where=db.text('type = {}'.format(PrincipalType.email))))
        indexes = [db.Index(None, 'mp_group_provider', 'mp_group_name')]
        checks = [_make_check(PrincipalType.user, cls.allow_emails, cls.allow_networks, 'user_id'),
                  _make_check(PrincipalType.local_group, cls.allow_emails, cls.allow_networks, 'local_group_id'),
                  _make_check(PrincipalType.multipass_group, cls.allow_emails, cls.allow_networks,
                              'mp_group_provider', 'mp_group_name')]
        if cls.allow_emails:
            checks.append(_make_check(PrincipalType.email, cls.allow_emails, cls.allow_networks, 'email'))
            checks.append(db.CheckConstraint('email IS NULL OR email = lower(email)', 'lowercase_email'))
        if cls.allow_networks:
            checks.append(_make_check(PrincipalType.network, cls.allow_emails, cls.allow_networks,
                                      'ip_network_group_id'))
        return tuple(uniques + indexes + checks)

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
    def type(cls):
        exclude_values = set()
        if not cls.allow_emails:
            exclude_values.add(PrincipalType.email)
        if not cls.allow_networks:
            exclude_values.add(PrincipalType.network)
        return db.Column(
            PyIntEnum(PrincipalType, exclude_values=(exclude_values or None)),
            nullable=False
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
    def email(cls):
        if not cls.allow_emails:
            return
        return db.Column(
            db.String,
            nullable=True,
            index=True
        )

    @declared_attr
    def ip_network_group_id(cls):
        if not cls.allow_networks:
            return
        return db.Column(
            db.Integer,
            db.ForeignKey('indico.ip_network_groups.id'),
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

    @declared_attr
    def ip_network_group(cls):
        if not cls.allow_networks:
            return
        assert cls.principal_backref_name
        return db.relationship(
            'IPNetworkGroup',
            lazy=False,
            backref=db.backref(
                cls.principal_backref_name,
                cascade='all, delete-orphan',
                lazy='dynamic'
            )
        )

    @hybrid_property
    def principal(self):
        from indico.modules.groups import GroupProxy
        if self.type == PrincipalType.user:
            return self.user
        elif self.type == PrincipalType.local_group:
            return self.local_group.proxy
        elif self.type == PrincipalType.multipass_group:
            return GroupProxy(self.multipass_group_name, self.multipass_group_provider)
        elif self.type == PrincipalType.email:
            return EmailPrincipal(self.email)
        elif self.type == PrincipalType.network:
            return self.ip_network_group

    @principal.setter
    def principal(self, value):
        self.type = value.principal_type
        self.email = None
        self.user = None
        self.local_group = None
        self.multipass_group_provider = self.multipass_group_name = None
        self.ip_network_group = None
        if self.type == PrincipalType.email:
            assert self.allow_emails
            self.email = value.email
        elif self.type == PrincipalType.network:
            assert self.allow_networks
            self.ip_network_group = value
        elif self.type == PrincipalType.local_group:
            self.local_group = value.group
        elif self.type == PrincipalType.multipass_group:
            self.multipass_group_provider = value.provider
            self.multipass_group_name = value.name
        elif self.type == PrincipalType.user:
            self.user = value
        else:
            raise ValueError('Unexpected principal type: {}'.format(self.type))

    @principal.comparator
    def principal(cls):
        return PrincipalComparator(cls)

    def merge_privs(self, other):
        """Merges the privileges of another principal

        :param other: Another principal object.
        """
        # nothing to do here

    def current_data(self):
        return None

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
        target_objects = {getattr(x, relationship_attr): x
                          for x in getattr(target, cls.principal_backref_name).options(joinedload(relationship))}
        for principal in source_principals:
            existing = target_objects.get(getattr(principal, relationship_attr))
            if existing is None:
                principal.user_id = target.id
            else:
                existing.merge_privs(principal)
                db.session.delete(principal)
        db.session.flush()

    @classmethod
    def replace_email_with_user(cls, user, relationship_attr):
        """
        Replaces all email-based entries matching the user's email
        addresses with user-based entries.
        If the user is already in the ACL, the two entries are merged.

        :param user: A User object.
        :param relationship_attr: The name of the relationship pointing
                                  to the object associated with the ACL
                                  entry.
        :return: The set of objects where the user has been added to
                 the ACL.
        """
        assert cls.allow_emails
        updated = set()
        query = (cls
                 .find(cls.email.in_(user.all_emails))
                 .options(noload('user'), noload('local_group'), joinedload(relationship_attr).load_only('id')))
        for entry in query:
            parent = getattr(entry, relationship_attr)
            existing = (cls.query
                        .with_parent(parent, 'acl_entries')
                        .options(noload('user'), noload('local_group'))
                        .filter_by(principal=user)
                        .first())
            if existing is None:
                entry.principal = user
            else:
                existing.merge_privs(entry)
                parent.acl_entries.remove(entry)
            updated.add(parent)
        db.session.flush()
        return updated


class PrincipalRolesMixin(PrincipalMixin):
    #: The model for which we are a principal.  May also be a string
    #: containing the model's class name.
    principal_for = None

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        checks = [db.CheckConstraint('read_access OR full_access OR array_length(roles, 1) IS NOT NULL', 'has_privs')]
        if cls.allow_networks:
            # you can match a network acl entry without being logged in.
            # we never want that for anything but simple read access
            checks.append(db.CheckConstraint('type != {} OR (NOT full_access AND array_length(roles, 1) IS NULL)'
                                             .format(PrincipalType.network),
                                             'networks_read_only'))
        return tuple(checks)

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

    def merge_privs(self, other):
        self.read_access = self.read_access or other.read_access
        self.full_access = self.full_access or other.full_access
        self.roles = sorted(set(self.roles) | set(other.roles))

    @property
    def current_data(self):
        return {'roles': set(self.roles),
                'read_access': self.read_access,
                'full_access': self.full_access}


class PrincipalComparator(Comparator):
    def __init__(self, cls):
        self.cls = cls

    def __clause_element__(self):
        # just in case
        raise NotImplementedError

    def __eq__(self, other):
        if other.principal_type == PrincipalType.email:
            criteria = [self.cls.email == other.email]
        elif other.principal_type == PrincipalType.network:
            criteria = [self.cls.ip_network_group_id == other.id]
        elif other.principal_type == PrincipalType.local_group:
            criteria = [self.cls.local_group_id == other.id]
        elif other.principal_type == PrincipalType.multipass_group:
            criteria = [self.cls.multipass_group_provider == other.provider,
                        self.cls.multipass_group_name == other.name]
        elif other.principal_type == PrincipalType.user:
            criteria = [self.cls.user_id == other.id]
        else:
            raise ValueError('Unexpected object type {}: {}'.format(type(other), other))
        return db.and_(self.cls.type == other.principal_type, *criteria)


def clone_principals(cls, principals):
    """Clone a list of principals.

    :param cls: the principal type to use (a `PrincipalMixin` subclass)
    :param principals: a collection of these principals
    :return: A new set of principals that can be added to an object
    """
    rv = set()
    assert all(isinstance(x, cls) for x in principals)
    attrs = get_simple_column_attrs(cls) | {'user', 'local_group', 'ip_network_group'}
    for old_principal in principals:
        principal = cls()
        principal.populate_from_dict({attr: getattr(old_principal, attr) for attr in attrs})
        rv.add(principal)
    return rv
