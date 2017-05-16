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
from sqlalchemy import type_coerce
from sqlalchemy.event import listens_for
from sqlalchemy.sql.schema import CheckConstraint
from sqlalchemy.sql.sqltypes import SchemaType, SmallInteger
from sqlalchemy.sql.type_api import TypeDecorator


class _EnumIntWrapper(int):
    """Int subclass that keeps the repr of the enum's member."""

    def __init__(self, enum_member):
        self.enum_member = enum_member
        super(_EnumIntWrapper, self).__init__(enum_member.value)

    def __repr__(self):
        return repr(self.enum_member)


class PyIntEnum(TypeDecorator, SchemaType):
    """Custom type which handles values from a PEP-435 Enum.

    In addition to the Python-side validation this also creates a
    CHECK constraint to ensure only valid enum members are stored.
    By default all enum members are allowed, but `exclude_values`
    can be used to exclude some.

    :param enum: the Enum repesented by this type's values
    :param exclude_values: a set of Enum values which are not allowed
    :raise ValueError: when using/loading a value not in the Enum.
    """

    impl = SmallInteger

    def __init__(self, enum=None, exclude_values=None):
        self.enum = enum
        self.exclude_values = set(exclude_values or ())
        TypeDecorator.__init__(self)
        SchemaType.__init__(self)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, self.enum):
            # Convert plain (int) value to enum member
            value = self.enum(value)
        return _EnumIntWrapper(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # Note: This raises a ValueError if `value` is not in the Enum.
        return self.enum(value)

    def coerce_set_value(self, value):
        if value is None:
            return None
        return self.enum(value)

    def alembic_render_type(self, autogen_context):
        autogen_context.imports.add('from indico.core.db.sqlalchemy import PyIntEnum')
        autogen_context.imports.add('from {} import {}'.format(self.enum.__module__, self.enum.__name__))
        if self.exclude_values:
            return '{}({}, exclude_values={{{}}})'.format(type(self).__name__, self.enum.__name__, ', '.join(
                '{}.{}'.format(self.enum.__name__, x.name) for x in sorted(self.exclude_values)
            ))
        else:
            return '{}({})'.format(type(self).__name__, self.enum.__name__)

    def marshmallow_get_field_kwargs(self):
        return {'enum': self.enum}


@listens_for(PyIntEnum, 'before_parent_attach')
def _type_before_parent_attach(type_, col):
    @listens_for(col, 'after_parent_attach')
    def _col_after_parent_attach(col, table):
        e = CheckConstraint(type_coerce(col, type_).in_(x.value for x in type_.enum if x not in type_.exclude_values),
                            'valid_enum_{}'.format(col.name))
        e.info['alembic_dont_render'] = True
        assert e.table is table
