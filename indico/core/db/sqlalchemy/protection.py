# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import has_request_context, session
from sqlalchemy import inspect
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.base import NEVER_SET, NO_VALUE

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.principals import EmailPrincipal, PrincipalType
from indico.core.permissions import get_available_permissions
from indico.util.caching import memoize_request
from indico.util.i18n import _
from indico.util.signals import values_from_signal
from indico.util.struct.enum import RichIntEnum
from indico.util.user import iter_acl
from indico.web.util import jsonify_template


class ProtectionMode(RichIntEnum):
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
    #: Whether the object can have an access key that grants read access
    allow_access_key = False
    #: Whether the object can have contact information shown in case of
    #: no access
    allow_no_access_contact = False

    @classmethod
    def register_protection_events(cls):
        """Registers sqlalchemy events needed by this mixin.

        Call this method after the definition of a model which uses
        this mixin class.
        """
        @listens_for(cls.protection_mode, 'set')
        def _set_protection_mode(target, value, oldvalue, *unused):
            if oldvalue in (NEVER_SET, NO_VALUE):
                return
            if value != oldvalue:
                signals.acl.protection_changed.send(type(target), obj=target, mode=value, old_mode=oldvalue)

    @declared_attr
    def protection_mode(cls):
        return db.Column(
            PyIntEnum(ProtectionMode, exclude_values=cls.disallowed_protection_modes),
            nullable=False,
            default=ProtectionMode.inheriting
        )

    @declared_attr
    def access_key(cls):
        if cls.allow_access_key:
            return db.Column(
                db.String,
                nullable=False,
                default=''
            )

    @declared_attr
    def own_no_access_contact(cls):
        if cls.allow_no_access_contact:
            return db.Column(
                'no_access_contact',
                db.String,
                nullable=False,
                default=''
            )

    @property
    def no_access_contact(self):
        return (self.own_no_access_contact
                if self.own_no_access_contact or not self.protection_parent
                else self.protection_parent.no_access_contact)

    @hybrid_property
    def is_public(self):
        return self.protection_mode == ProtectionMode.public

    @hybrid_property
    def is_inheriting(self):
        return self.protection_mode == ProtectionMode.inheriting

    @hybrid_property
    def is_self_protected(self):
        """Checks whether the object itself is protected.

        If you also care about inherited protection from a parent,
        use `is_protected` instead.
        """
        return self.protection_mode == ProtectionMode.protected

    @property
    def is_protected(self):
        """
        Checks whether ths object is protected, either by itself or
        by inheriting from a protected object.
        """
        if self.is_inheriting:
            return self.protection_parent.is_protected
        else:
            return self.is_self_protected

    @property
    def protection_repr(self):
        protection_mode = self.protection_mode.name if self.protection_mode is not None else None
        return 'protection_mode={}'.format(protection_mode)

    @property
    def protection_parent(self):
        """The parent object to consult for ProtectionMode.inheriting"""
        raise NotImplementedError

    def _check_can_access_override(self, user, allow_admin, authorized=None):
        # Trigger signals for protection overrides
        rv = values_from_signal(signals.acl.can_access.send(type(self), obj=self, user=user, allow_admin=allow_admin,
                                                            authorized=authorized),
                                single_value=True)
        # in case of contradictory results (shouldn't happen at all)
        # we stay on the safe side and deny access
        return all(rv) if rv else None

    @memoize_request
    def can_access(self, user, allow_admin=True):
        """Checks if the user can access the object.

        :param user: The :class:`.User` to check. May be None if the
                     user is not logged in.
        :param allow_admin: If admin users should always have access
        """

        override = self._check_can_access_override(user, allow_admin=allow_admin)
        if override is not None:
            return override

        # Usually admins can access everything, so no need for checks
        if allow_admin and user and user.is_admin:
            rv = True
        # If there's a valid access key we can skip all other ACL checks
        elif self.allow_access_key and self.check_access_key():
            rv = True
        elif self.protection_mode == ProtectionMode.public:
            # if it's public we completely ignore the parent protection
            # this is quite ugly which is why it should only be allowed
            # in rare cases (e.g. events which might be in a protected
            # category but should be public nonetheless)
            rv = True
        elif self.protection_mode == ProtectionMode.protected:
            # if it's protected, we also ignore the parent protection
            # and only check our own ACL
            if any(user in entry.principal for entry in iter_acl(self.acl_entries)):
                rv = True
            elif isinstance(self, ProtectionManagersMixin):
                rv = self.can_manage(user, allow_admin=allow_admin)
            else:
                rv = False
        elif self.protection_mode == ProtectionMode.inheriting:
            # if it's inheriting, we only check the parent protection
            # unless `inheriting_have_acl` is set, in which case we
            # might not need to check the parents at all
            if self.inheriting_have_acl and any(user in entry.principal for entry in iter_acl(self.acl_entries)):
                rv = True
            else:
                # the parent can be either an object inheriting from this
                # mixin or a legacy object with an AccessController
                parent = self.protection_parent
                if parent is None:
                    # This should be the case for the top-level object,
                    # i.e. the root category, which shouldn't allow
                    # ProtectionMode.inheriting as it makes no sense.
                    raise TypeError('protection_parent of {} is None'.format(self))
                elif hasattr(parent, 'can_access'):
                    rv = parent.can_access(user, allow_admin=allow_admin)
                else:
                    raise TypeError('protection_parent of {} is of invalid type {} ({})'.format(self, type(parent),
                                                                                                parent))
        else:
            # should never happen, but since this is a sensitive area
            # we better fail loudly if we have garbage
            raise ValueError('Invalid protection mode: {}'.format(self.protection_mode))

        override = self._check_can_access_override(user, allow_admin=allow_admin, authorized=rv)
        return override if override is not None else rv

    def check_access_key(self, access_key=None):
        """Check whether an access key is valid for the object.

        :param access_key: Use the given access key instead of taking
                           it from the session.
        """
        assert self.allow_access_key
        if not self.access_key:
            return False
        if access_key is None:
            if not has_request_context():
                return False
            access_key = session.get('access_keys', {}).get(self._access_key_session_key)
        if not access_key:
            return False
        return self.access_key == access_key

    def set_session_access_key(self, access_key):
        """Store an access key for the object in the session.

        :param access_key: The access key to store. It is not checked
                           for validity.
        """
        assert self.allow_access_key
        session.setdefault('access_keys', {})[self._access_key_session_key] = access_key
        session.modified = True

    @property
    def _access_key_session_key(self):
        cls, pks = inspect(self).identity_key[:2]
        return '{}-{}'.format(cls.__name__, '-'.join(map(unicode, pks)))

    def update_principal(self, principal, read_access=None, quiet=False):
        """Updates access privileges for the given principal.

        :param principal: A `User`, `GroupProxy` or `EmailPrincipal` instance.
        :param read_access: If the principal should have explicit read
                            access to the object.
        :param quiet: Whether the ACL change should happen silently.
                      This indicates to acl change signal handlers
                      that the change should not be logged, trigger
                      emails or result in similar notifications.
        :return: The ACL entry for the given principal or ``None`` if
                 he was removed (or not added).
        """
        principal = _resolve_principal(principal)
        principal_class, entry = _get_acl_data(self, principal)
        if entry is None and read_access:
            entry = principal_class(principal=principal)
            self.acl_entries.add(entry)
            signals.acl.entry_changed.send(type(self), obj=self, principal=principal, entry=entry, is_new=True,
                                           old_data=None, quiet=quiet)
            return entry
        elif entry is not None and not read_access:
            self.acl_entries.remove(entry)
            # Flush in case the same principal is added back afterwards.
            # Not flushing in other cases (adding/modifying) is intentional
            # as this might happen on a newly created object which is not yet
            # flushable due to missing data
            db.session.flush()
            signals.acl.entry_changed.send(type(self), obj=self, principal=principal, entry=None, is_new=False,
                                           old_data=None, quiet=quiet)
            return None
        return entry

    def remove_principal(self, principal, quiet=False):
        """Revokes all access privileges for the given principal.

        This method doesn't do anything if the user is not in the
        object's ACL.

        :param principal: A `User`, `GroupProxy` or `EmailPrincipal` instance.
        :param quiet: Whether the ACL change should happen silently.
                      This indicates to acl change signal handlers
                      that the change should not be logged, trigger
                      emails or result in similar notifications.
        """
        principal = _resolve_principal(principal)
        entry = _get_acl_data(self, principal)[1]
        if entry is not None:
            signals.acl.entry_changed.send(type(self), obj=self, principal=principal, entry=None, is_new=False,
                                           old_data=entry.current_data, quiet=quiet)
            self.acl_entries.remove(entry)

    def get_inherited_acl(self):
        own_acl = {entry.principal for entry in self.acl_entries}
        parent_acl = self.protection_parent.get_access_list(skip_managers=True)
        return [x for x in parent_acl if x not in own_acl]


class ProtectionManagersMixin(ProtectionMixin):
    @property
    def all_manager_emails(self):
        """Return the emails of all managers"""
        # We ignore email principals here. They never signed up in indico anyway...
        return {p.principal.email
                for p in self.acl_entries
                if p.type == PrincipalType.user and p.has_management_permission()}

    @memoize_request
    def can_manage(self, user, permission=None, allow_admin=True, check_parent=True, explicit_permission=False):
        """Checks if the user can manage the object.

        :param user: The :class:`.User` to check. May be None if the
                     user is not logged in.
        :param: permission: The management permission that is needed for
                            the check to succeed.  If not specified, full
                            management privs are required.  May be set to
                            the string ``'ANY'`` to check if the user has
                            any management privileges.  If the user has
                            `full_access` privileges, he's assumed to have
                            all possible permissions.
        :param allow_admin: If admin users should always have access
        :param check_parent: If the parent object should be checked.
                             In this case the permission is ignored; only
                             full management access is inherited to
                             children.
        :param explicit_permission: If the specified permission should be checked
                                    explicitly instead of short-circuiting
                                    the check for Indico admins or managers.
                                    When this option is set to ``True``, the
                                    values of `allow_admin` and `check_parent`
                                    are ignored.  This also applies if `permission`
                                    is None in which case this argument being
                                    set to ``True`` is equivalent to
                                    `allow_admin` and `check_parent` being set
                                    to ``False``.
        """
        if permission is not None and permission != 'ANY' and permission not in get_available_permissions(type(self)):
            raise ValueError("permission '{}' is not valid for '{}' objects".format(permission, type(self).__name__))

        if user is None:
            # An unauthorized user is never allowed to perform management operations.
            # Not even signals may override this since management code generally
            # expects session.user to be not None.
            return False

        # Trigger signals for protection overrides
        rv = values_from_signal(signals.acl.can_manage.send(type(self), obj=self, user=user, permission=permission,
                                                            allow_admin=allow_admin, check_parent=check_parent,
                                                            explicit_permission=explicit_permission),
                                single_value=True)
        if rv:
            # in case of contradictory results (shouldn't happen at all)
            # we stay on the safe side and deny access
            return all(rv)

        # Usually admins can access everything, so no need for checks
        if not explicit_permission and allow_admin and user.is_admin:
            return True

        if any(user in entry.principal
               for entry in iter_acl(self.acl_entries)
               if entry.has_management_permission(permission,
                                                  explicit=(explicit_permission and permission is not None))):
            return True

        if not check_parent or explicit_permission:
            return False

        # the parent can be either an object inheriting from this
        # mixin or a legacy object with an AccessController
        parent = self.protection_parent
        if parent is None:
            # This should be the case for the top-level object,
            # i.e. the root category
            return False
        elif hasattr(parent, 'can_manage'):
            return parent.can_manage(user, allow_admin=allow_admin)
        else:
            raise TypeError('protection_parent of {} is of invalid type {} ({})'.format(self, type(parent), parent))

    def update_principal(self, principal, read_access=None, full_access=None, permissions=None, add_permissions=None,
                         del_permissions=None, quiet=False):
        """Updates access privileges for the given principal.

        If the principal is not in the ACL, it will be added if
        necessary.  If the changes remove all its privileges, it
        will be removed from the ACL.

        :param principal: A `User`, `GroupProxy` or `EmailPrincipal` instance.
        :param read_access: If the principal should have explicit read
                            access to the object.  This does not grant
                            any management permissions - it simply
                            grants access to an otherwise protected
                            object.
        :param full_access: If the principal should have full management
                            access.
        :param permissions: set -- The management permissions to grant.
                            Any existing permissions will be replaced.
        :param add_permissions: set -- Management permissions to add.
        :param del_permissions: set -- Management permissions to remove.
        :param quiet: Whether the ACL change should happen silently.
                      This indicates to acl change signal handlers
                      that the change should not be logged, trigger
                      emails or result in similar notifications.
        :return: The ACL entry for the given principal or ``None`` if
                 he was removed (or not added).
        """
        if permissions is not None and (add_permissions or del_permissions):
            raise ValueError('add_permissions/del_permissions and permissions are mutually exclusive')
        principal = _resolve_principal(principal)
        principal_class, entry = _get_acl_data(self, principal)
        new_entry = False
        if entry is None:
            if not permissions and not add_permissions and not full_access and not read_access:
                # not in ACL and no permissions to add
                return None
            entry = principal_class(principal=principal, read_access=False, full_access=False, permissions=[])
            self.acl_entries.add(entry)
            new_entry = True
        old_data = entry.current_data
        # update permissions
        new_permissions = set(entry.permissions)
        if permissions is not None:
            new_permissions = permissions
        else:
            if add_permissions:
                new_permissions |= add_permissions
            if del_permissions:
                new_permissions -= del_permissions
        invalid_permissions = new_permissions - get_available_permissions(type(self)).viewkeys()
        if invalid_permissions:
            raise ValueError('Invalid permissions: {}'.format(', '.join(invalid_permissions)))
        entry.permissions = sorted(new_permissions)
        # update read privs
        if read_access is not None:
            entry.read_access = read_access
        # update full management privs
        if full_access is not None:
            entry.full_access = full_access
        # remove entry from acl if no privileges
        if not entry.read_access and not entry.full_access and not entry.permissions:
            self.acl_entries.remove(entry)
            # Flush in case the same principal is added back afterwards.
            # Not flushing in other cases (adding/modifying) is intentional
            # as this might happen on a newly created object which is not yet
            # flushable due to missing data
            db.session.flush()
            signals.acl.entry_changed.send(type(self), obj=self, principal=principal, entry=None, is_new=False,
                                           old_data=old_data, quiet=quiet)
            return None
        signals.acl.entry_changed.send(type(self), obj=self, principal=principal, entry=entry, is_new=new_entry,
                                       old_data=old_data, quiet=quiet)
        return entry

    def get_manager_list(self, recursive=False):
        managers = {x.principal for x in self.acl_entries if x.has_management_permission()}
        if recursive and self.protection_parent:
            managers.update(self.protection_parent.get_manager_list(recursive=True))
        return managers

    def get_access_list(self, skip_managers=False, skip_self_acl=False):
        read_access_list = {x.principal for x in self.acl_entries if x.read_access} if not skip_self_acl else set()
        if self.is_self_protected:
            return (read_access_list | self.get_manager_list(recursive=True)) if not skip_managers else read_access_list
        elif self.is_inheriting and self.is_protected:
            access_list = (read_access_list | self.get_manager_list()) if not skip_managers else read_access_list
            if self.protection_parent:
                access_list.update(self.protection_parent.get_access_list(skip_managers=skip_managers))
            return access_list
        else:
            return set()


def _get_acl_data(obj, principal):
    """Helper function to get the necessary data for ACL modifications

    :param obj: A `ProtectionMixin` instance
    :param principal: A User or GroupProxy uinstance
    :return: A tuple containing the principal class and the existing
             ACL entry for the given principal if it exists.
    """
    principal_class = type(obj).acl_entries.prop.mapper.class_
    entry = next((x for x in obj.acl_entries if x.principal == principal), None)
    return principal_class, entry


def _resolve_principal(principal):
    """Helper function to convert an email principal to a user if possible

    :param principal: A `User`, `GroupProxy` or `EmailPrincipal` instance.
    """
    if isinstance(principal, EmailPrincipal):
        return principal.user or principal
    return principal


def render_acl(obj):
    return jsonify_template('_access_list.html', acl=obj.get_inherited_acl())
