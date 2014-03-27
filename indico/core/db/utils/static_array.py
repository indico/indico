# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from StringIO import StringIO

from sqlalchemy import types
from sqlalchemy import String
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles

class StaticArray(types.TypeDecorator):
    impl = types.TypeEngine

    def __init__(self):
        super(StaticArray, self).__init__()
        import sqlalchemy.dialects.postgresql.base as pg
        self.__supported = {pg.PGDialect:pg.PGArray}
        del pg

    def load_dialect_impl(self, dialect):
        if dialect.__class__ in self.__supported:
            return self.__supported[dialect.__class__](String)
        else:
            return dialect.type_descriptor(String)

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return tuple(value)

    def is_mutable(self):
        return False

class array_agg(expression.ColumnElement):
    type = StaticArray()

    def __init__(self, expr, order_by=None):
        self.expr = expression._literal_as_binds(expr)

        if order_by is not None:
            self.order_by = expression._literal_as_binds(order_by)
        else:
            self.order_by = None


@compiles(array_agg, 'postgresql')
def _compile_array_agg_postgresql(element, compiler, **kw):
    buf = StringIO()
    buf.write('array_agg(')
    buf.write(compiler.process(element.expr))
    if element.order_by is not None:
        buf.write(' ORDER BY ')
        buf.write(compiler.process(element.order_by))
    buf.write(')')
    return buf.getvalue()
