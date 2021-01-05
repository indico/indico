# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import

import sys
from contextlib import contextmanager
from functools import partial

from flask import g
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.model import BindMetaMixin
from sqlalchemy.event import listen
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import CompositeProperty, mapper
from sqlalchemy.sql.ddl import CreateSchema

from indico.core import signals
from indico.core.db.sqlalchemy.custom.natsort import create_natsort_function
from indico.core.db.sqlalchemy.custom.unaccent import create_unaccent_function
from indico.core.db.sqlalchemy.util.models import IndicoBaseQuery, IndicoModel


class ConstraintViolated(Exception):
    """Indicate that a constraint trigger was violated."""
    def __init__(self, message, orig):
        super(ConstraintViolated, self).__init__(message)
        self.orig = orig


def handle_sqlalchemy_database_error():
    """Handle a SQLAlchemy DatabaseError exception nicely.

    Currently this only takes care of custom INDX exception
    raised from constraint triggers.  It must be invoked from an
    ``except DatabaseError`` block.

    :raise ConstraintViolated: if an exception with an SQLSTATE of
                               ``INDX*`` has been thrown.  This is
                               used in custom constraint triggers
                               that enforce consistenct
    :raise DatabaseError: any other database error is simply re-raised
    """
    exc_class, exc, tb = sys.exc_info()
    if exc.orig.pgcode is None or not exc.orig.pgcode.startswith('INDX'):
        # not an indico exception
        raise
    msg = exc.orig.diag.message_primary
    if exc.orig.diag.message_detail:
        msg += ': {}'.format(exc.orig.diag.message_detail)
    if exc.orig.diag.message_hint:
        msg += ' ({})'.format(exc.orig.diag.message_hint)
    raise ConstraintViolated(msg, exc.orig), None, tb  # raise with original traceback


def _after_commit(*args, **kwargs):
    signals.after_commit.send()
    if hasattr(g, 'memoize_cache'):
        del g.memoize_cache


class IndicoSQLAlchemy(SQLAlchemy):
    def __init__(self, *args, **kwargs):
        super(IndicoSQLAlchemy, self).__init__(*args, **kwargs)
        self.m = type(b'_Models', (object,), {})

    def create_session(self, *args, **kwargs):
        session = super(IndicoSQLAlchemy, self).create_session(*args, **kwargs)
        listen(session, 'after_commit', _after_commit)
        return session

    def enforce_constraints(self):
        """Enable immediate enforcing of deferred constraints.

        This should be done at the end of normal request processing
        and exceptions should be handled in a clean way that goes
        beyond letting the user report an error.  If you do not expect
        a deferred constraint to be violated do not use this - the
        constraints will be checked at commit time and result in an
        error if there are any violations.

        Constraints will revert to their default deferred mode once
        the active transaction ends, i.e. on rollback or commit.

        Exceptions from custom constraint triggers will raise
        `ConstraintViolated`.
        """
        self.session.flush()
        try:
            self.session.execute('SET CONSTRAINTS ALL IMMEDIATE')
        except DatabaseError:
            handle_sqlalchemy_database_error()

    @contextmanager
    def tmp_session(self):
        """Provide a contextmanager with a temporary SQLAlchemy session.

        This allows you to use SQLAlchemy e.g. in a `after_this_request`
        callback without having to worry about things like the ZODB extension,
        implicit commits, etc.
        """
        session = db.create_session({'query_cls': IndicoBaseQuery})()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


class NoNameGenMeta(BindMetaMixin, DeclarativeMeta):
    # This is like Flask-SQLAlchemy's default metaclass but without
    # generating table names (i.e. a model without an explicit table
    # name will fail instead of getting a name set implicitly)
    pass


def _schema_exists(connection, name):
    sql = 'SELECT COUNT(*) FROM "information_schema"."schemata" WHERE "schema_name" = :name'
    count = connection.execute(db.text(sql), name=name).scalar()
    return bool(count)


def _before_create(target, connection, **kw):
    # SQLAlchemy doesn't create schemas so we need to take care of it...
    schemas = {table.schema for table in kw['tables']}
    for schema in schemas:
        if not _schema_exists(connection, schema):
            CreateSchema(schema).execute(connection)
            signals.db_schema_created.send(unicode(schema), connection=connection)
    # Create our custom functions
    create_unaccent_function(connection)
    create_natsort_function(connection)


def _mapper_configured(mapper, class_):
    # Make model available via db.m.*
    setattr(db.m, class_.__name__, class_)

    # Create a setter listener to coerce attribute values for custom types supporting it
    def _coerce_custom(target, value, oldvalue, initiator, fn):
        return fn(value)

    for prop in mapper.iterate_properties:
        if hasattr(prop, 'columns') and not isinstance(prop, CompositeProperty):
            func = getattr(prop.columns[0].type, 'coerce_set_value', None)
            if func is not None:
                # Using partial here to avoid closure scoping issues
                listen(getattr(class_, prop.key), 'set', partial(_coerce_custom, fn=func), retval=True)


def _column_names(constraint, table):
    return '_'.join((c if isinstance(c, basestring) else c.name) for c in constraint.columns)


def _unique_index(constraint, table):
    return 'uq_' if constraint.unique else ''


naming_convention = {
    'fk': 'fk_%(table_name)s_%(column_names)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
    'ix': 'ix_%(unique_index)s%(table_name)s_%(column_names)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'uq': 'uq_%(table_name)s_%(column_names)s',
    'column_names': _column_names,
    'unique_index': _unique_index
}

db = IndicoSQLAlchemy(model_class=declarative_base(cls=IndicoModel, metaclass=NoNameGenMeta, name='Model'),
                      query_class=IndicoBaseQuery)
db.Model.metadata.naming_convention = naming_convention
listen(db.Model.metadata, 'before_create', _before_create)
listen(mapper, 'mapper_configured', _mapper_configured)
