# Based on https://groups.google.com/d/topic/sqlalchemy/cQ9e9IVOykE/discussion
# By David Gardner (dgardner@creatureshop.com)

"""
StaticArray class and functions that SQLAlchemy can process instead of non hashable lists
"""

from cStringIO import StringIO

from sqlalchemy import types, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles


class StaticArray(types.TypeDecorator):
    impl = types.TypeEngine

    def __init__(self):
        super(StaticArray, self).__init__()
        self.__supported = {PGDialect: ARRAY}

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
    buf.write('array(select x from unnest(array_agg(')
    buf.write(compiler.process(element.expr))
    if element.order_by is not None:
        buf.write(' ORDER BY ')
        buf.write(compiler.process(element.order_by))
    buf.write(')) x WHERE x IS NOT NULL)')
    return buf.getvalue()


class array(expression.ColumnElement):
    type = StaticArray()

    def __init__(self, expr):
        self.expr = expression._literal_as_binds(expr)


@compiles(array, 'postgresql')
def _compile_array_postgresql(element, compiler, **kw):
    buf = StringIO()
    buf.write('array(')
    buf.write(compiler.process(element.expr))
    buf.write(')')
    return buf.getvalue()
