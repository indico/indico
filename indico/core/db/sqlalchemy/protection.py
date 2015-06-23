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

from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db import db
from indico.util.i18n import _
from indico.util.struct.enum import TitledIntEnum


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
