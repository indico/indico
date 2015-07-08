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
from indico.util.i18n import _
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

    def can_access(self, user, acl_attr='acl', legacy_method='canAccess', allow_admin=True):
        """Checks if the user can access the object.

        When using a custom `acl_attr` on an object that supports
        inherited proection, ALL possible `protection_parent` objects
        need to have an ACL with the same name too!

        :param user: The :class:`.User` to check. May be None if the
                     user is not logged in.
        :param acl_attr: The name of the property that contains the
                         set of authorized principals.
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
            return any(user in principal for principal in iter_acl(getattr(self, acl_attr)))
        elif self.protection_mode == ProtectionMode.inheriting:
            # if it's inheriting, we only check the parent protection.
            # the parent can be either an object inheriting from this
            # mixin or a legacy object with an AccessController
            parent = self.protection_parent
            if parent is None:
                # This should be the case for the top-level object,
                # i.e. the root category, which shouldn't allow
                # ProtectionMode.inheriting as it makes no sense.
                raise TypeError('protection_parent of {} is None'.format(self))
            elif hasattr(parent, 'can_access'):
                return parent.can_access(user, acl_attr=acl_attr)
            elif legacy_method is not None and hasattr(parent, legacy_method):
                return getattr(parent, legacy_method)(AccessWrapper(user.as_avatar if user else None))
            else:
                raise TypeError('protection_parent of {} is of invalid type {} ({})'.format(self, type(parent), parent))
        else:
            # should never happen, but since this is a sensitive area
            # we better fail loudly if we have garbage
            raise ValueError('Invalid protection mode: {}'.format(self.protection_mode))
