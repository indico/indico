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
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core import signals
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db import db
from indico.core.roles import get_available_roles
from indico.util.i18n import _
from indico.util.caching import memoize_request
from indico.util.signals import values_from_signal
from indico.util.struct.enum import TitledIntEnum
from indico.util.user import iter_acl
from MaKaC.accessControl import AccessWrapper


class ProtectionMode(TitledIntEnum):
    __titles__ = [_('Public'), _('Inheriting'), _('Protected')]
    public = 0
    inheriting = 1
    protected = 2


class ProtectionMixin(object):
    #: The protection modes that are not allowed.  Can be overridden
    #: in the model that is using the mixin.  Affects the table
    #: structure, so any changes to it should go along with a migration
    #: step!  By default, the `public` mode is disallowed since it does
    #: not make much sense in most cases to make something public even
    #: though its parent object is private (or inheriting).
    disallowed_protection_modes = frozenset({ProtectionMode.public})
    #: Whether objects with inheriting protection may have their own
    #: ACL entries (which will grant access even if the user cannot
    #: access the parent object).
    inheriting_have_acl = False

    @declared_attr
    def protection_mode(cls):
        return db.Column(
            PyIntEnum(ProtectionMode, exclude_values=cls.disallowed_protection_modes),
            nullable=False,
            default=ProtectionMode.inheriting
        )

    @hybrid_property
    def is_public(self):
        return self.protection_mode == ProtectionMode.public

    @hybrid_property
    def is_inheriting(self):
        return self.protection_mode == ProtectionMode.inheriting

    @hybrid_property
    def is_protected(self):
        return self.protection_mode == ProtectionMode.protected

    @property
    def protection_repr(self):
        protection_mode = self.protection_mode.name if self.protection_mode is not None else None
        return 'protection_mode={}'.format(protection_mode)

    @property
    def protection_parent(self):
        """The parent object to consult for ProtectionMode.inheriting"""
        raise NotImplementedError

    @memoize_request
    def can_access(self, user, acl_attr='acl_entries', legacy_method='canAccess', allow_admin=True):
        """Checks if the user can access the object.

        When using a custom `acl_attr` on an object that supports
        inherited proection, ALL possible `protection_parent` objects
        need to have an ACL with the same name too!

        :param user: The :class:`.User` to check. May be None if the
                     user is not logged in.
        :param acl_attr: The name of the relationship that contains the
                         ACL of the object.
        :param legacy_method: The method name to use when inheriting
                              the protection from a legacy object.
        :param allow_admin: If admin users should always have access
        """

        # Trigger signals for protection overrides
        rv = values_from_signal(signals.acl.can_access.send(type(self), obj=self, user=user, acl_attr=acl_attr,
                                                            legacy_method=legacy_method, allow_admin=allow_admin),
                                single_value=True)
        if rv:
            # in case of contradictory results (shouldn't happen at all)
            # we stay on the safe side and deny access
            return all(rv)

        # Usually admins can access everything, so no need for checks
        if allow_admin and user and user.is_admin:
            return True

        if self.protection_mode == ProtectionMode.public:
            # if it's public we completely ignore the parent protection
            # this is quite ugly which is why it should only be allowed
            # in rare cases (e.g. events which might be in a protected
            # category but should be public nonetheless)
            return True
        elif self.protection_mode == ProtectionMode.protected:
            # if it's protected, we also ignore the parent protection
            # and only check our own ACL
            return any(user in entry.principal for entry in iter_acl(getattr(self, acl_attr)))
        elif self.protection_mode == ProtectionMode.inheriting:
            # if it's inheriting, we only check the parent protection
            # unless `inheriting_have_acl` is set, in which case we
            # might not need to check the parents at all
            if (self.inheriting_have_acl and
                    any(user in entry.principal for entry in iter_acl(getattr(self, acl_attr)))):
                return True
            # the parent can be either an object inheriting from this
            # mixin or a legacy object with an AccessController
            parent = self.protection_parent
            if parent is None:
                # This should be the case for the top-level object,
                # i.e. the root category, which shouldn't allow
                # ProtectionMode.inheriting as it makes no sense.
                raise TypeError('protection_parent of {} is None'.format(self))
            elif hasattr(parent, 'can_access'):
                return parent.can_access(user, acl_attr=acl_attr, legacy_method=legacy_method, allow_admin=allow_admin)
            elif legacy_method is not None and hasattr(parent, legacy_method):
                return getattr(parent, legacy_method)(AccessWrapper(user.as_avatar if user else None))
            else:
                raise TypeError('protection_parent of {} is of invalid type {} ({})'.format(self, type(parent), parent))
        else:
            # should never happen, but since this is a sensitive area
            # we better fail loudly if we have garbage
            raise ValueError('Invalid protection mode: {}'.format(self.protection_mode))

    def update_principal(self, principal, read_access=None, acl_attr='acl_entries'):
        """Updates access privileges for the given principal.

        :param principal: A `User` or `GroupProxy` instance.
        :param read_access: If the principal should have explicit read
                            access to the object.
        :param acl_attr: The name of the relationship that contains the
                         ACL of the object.
        :return: The ACL entry for the given principal or ``None`` if
                 he was removed (or not added).
        """
        acl_rel, principal_class, entry = _get_acl_data(self, acl_attr, principal)
        if entry is None and read_access:
            entry = principal_class(principal=principal)
            acl_rel.add(entry)
            signals.acl.entry_changed.send(type(self), obj=self, principal=principal, entry=entry)
            return entry
        elif entry is not None and not read_access:
            acl_rel.remove(entry)
            signals.acl.entry_changed.send(type(self), obj=self, principal=principal, entry=None)
            return None
        return entry

    def remove_principal(self, principal, acl_attr='acl_entries'):
        """Revokes all access privileges for the given principal.

        This method doesn't do anything if the user is not in the
        object's ACL.

        :param principal: A `User` or `GroupProxy` instance.
        :param acl_attr: The name of the relationship that contains the
                         ACL of the object.
        """
        acl_rel, _, entry = _get_acl_data(self, acl_attr, principal)
        if entry is not None:
            signals.acl.entry_changed.send(type(self), obj=self, principal=principal, entry=None)
            acl_rel.remove(entry)


class ProtectionManagersMixin(ProtectionMixin):
    @memoize_request
    def can_manage(self, user, role=None, acl_attr='acl_entries', legacy_method='canUserModify', allow_admin=True,
                   check_parent=True, explicit=False):
        """Checks if the user can manage the object.

        When using a custom `acl_attr`, ALL possible `protection_parent`
        objects need to have an ACL with the same name too!

        :param user: The :class:`.User` to check. May be None if the
                     user is not logged in.
        :param: role: The management role that is needed for the
                      check to succeed.  If not specified, full
                      management privs are required.  May be set to
                      the string ``'ANY'`` to check if the user has
                      any management privileges.  Full management
                      privs always grant access even if the role is
                      not granted explicitly.
        :param acl_attr: The name of the relationship that contains the
                         ACL of the object.
        :param legacy_method: The method name to use when inheriting
                              the protection from a legacy object.
        :param allow_admin: If admin users should always have access
        :param check_parent: If the parent object should be checked.
                             In this case the role is ignored; only
                             full management access is inherited to
                             children.
        :param explicit: If the specified role should be checked
                         explicitly instead of short-circuiting
                         the check for Indico admins or managers.
                         When this option is set to ``True``, the
                         values of `allow_admin` and `check_parent`
                         are ignored.
        """
        if role is not None and role != 'ANY' and role not in get_available_roles(type(self)):
            raise ValueError("role '{}' is not valid for '{}' objects".format(role, type(self).__name__))

        # Trigger signals for protection overrides
        rv = values_from_signal(signals.acl.can_manage.send(type(self), obj=self, user=user, role=role,
                                                            acl_attr=acl_attr, legacy_method=legacy_method,
                                                            allow_admin=allow_admin, check_parent=check_parent,
                                                            explicit=explicit),
                                single_value=True)
        if rv:
            # in case of contradictory results (shouldn't happen at all)
            # we stay on the safe side and deny access
            return all(rv)

        # Usually admins can access everything, so no need for checks
        if not explicit and allow_admin and user and user.is_admin:
            return True

        if any(user in entry.principal
               for entry in iter_acl(getattr(self, acl_attr))
               if entry.has_management_role(role, explicit=explicit)):
            return True

        if not check_parent or explicit:
            return False

        # the parent can be either an object inheriting from this
        # mixin or a legacy object with an AccessController
        parent = self.protection_parent
        if parent is None:
            # This should be the case for the top-level object,
            # i.e. the root category
            return False
        elif hasattr(parent, 'can_manage'):
            return parent.can_manage(user, acl_attr=acl_attr, legacy_method=legacy_method, allow_admin=allow_admin)
        elif legacy_method is not None and hasattr(parent, legacy_method):
            return getattr(parent, legacy_method)(user.as_avatar if user else None)
        else:
            raise TypeError('protection_parent of {} is of invalid type {} ({})'.format(self, type(parent), parent))

    def update_principal(self, principal, read_access=None, full_access=None, roles=None, add_roles=None,
                         del_roles=None, acl_attr='acl_entries'):
        """Updates access privileges for the given principal.

        If the principal is not in the ACL, it will be added if
        necessary.  If the changes remove all its privileges, it
        will be removed from the ACL.

        :param principal: A `User` or `GroupProxy` instance.
        :param read_access: If the principal should have explicit read
                            access to the object.  This does not grant
                            any management permissions - it simply
                            grants access to an otherwise protected
                            object.
        :param full_access: If the principal should have full management
                            access.
        :param roles: set -- The management roles to grant.  Any
                      existing roles will be replaced.
        :param add_roles: set -- Management roles to add.
        :param del_roles: set -- Management roles to remove.
        :param acl_attr: The name of the relationship that contains the
                         ACL of the object.
        :return: The ACL entry for the given principal or ``None`` if
                 he was removed (or not added).
        """
        if roles is not None and (add_roles or del_roles):
            raise ValueError('add_roles/del_roles and roles are mutually exclusive')
        acl_rel, principal_class, entry = _get_acl_data(self, acl_attr, principal)
        if entry is None:
            if not roles and not add_roles and not full_access and not read_access:
                # not in ACL and no permissions to add
                return None
            entry = principal_class(principal=principal, read_access=False, full_access=False, roles=[])
            acl_rel.add(entry)
        # update roles
        new_roles = set(entry.roles)
        if roles is not None:
            new_roles &= roles
        else:
            if add_roles:
                new_roles |= add_roles
            if del_roles:
                new_roles -= del_roles
        entry.roles = sorted(new_roles)
        # update read privs
        if read_access is not None:
            entry.read_access = read_access
        # update full management privs
        if full_access is not None:
            entry.full_access = full_access
        # remove entry from acl if no privileges
        if not entry.read_access and not entry.full_access and not entry.roles:
            acl_rel.remove(entry)
            signals.acl.entry_changed.send(type(self), obj=self, principal=principal, entry=None)
            return None
        signals.acl.entry_changed.send(type(self), obj=self, principal=principal, entry=entry)
        return entry


def _get_acl_data(obj, acl_attr, principal):
    """Helper function to get the necessary data for ACL modifications

    :param obj: A `ProtectionMixin` instance
    :param acl_attr: The name of the relationship that contains the
                     ACL of the object.
    :param principal: A User or GroupProxy uinstance
    :return: A tuple containing the ACL relationship, the principal
             class and the existing ACL entry for the given principal.
    """
    acl_rel = getattr(obj, acl_attr)
    principal_class = getattr(type(obj), acl_attr).prop.mapper.class_
    entry = next((x for x in acl_rel if x.principal == principal), None)
    return acl_rel, principal_class, entry
