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

from __future__ import absolute_import

from contextlib import contextmanager

import logging
import sys
from functools import partial

import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.event import listen
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import mapper, CompositeProperty
from sqlalchemy.sql.ddl import CreateSchema
from werkzeug.utils import cached_property

from indico.core import signals
from indico.core.db.sqlalchemy.custom.unaccent import create_unaccent_function

# Monkeypatching this since Flask-SQLAlchemy doesn't let us override the model class
from indico.core.db.sqlalchemy.util.models import IndicoModel, IndicoBaseQuery
flask_sqlalchemy.Model = IndicoModel
flask_sqlalchemy.BaseQuery = IndicoBaseQuery


class ConstraintViolated(Exception):
    """Indicates that a constraint trigger was violated"""
    def __init__(self, message, orig):
        super(ConstraintViolated, self).__init__(message)
        self.orig = orig


def handle_sqlalchemy_database_error():
    """Handle a SQLAlchemy DatabaseError exception nicely

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
    raise ConstraintViolated, (msg, exc.orig), tb  # raise with original traceback


class IndicoSQLAlchemy(SQLAlchemy):
    def __init__(self, *args, **kwargs):
        super(IndicoSQLAlchemy, self).__init__(*args, **kwargs)
        self.m = type(b'_Models', (object,), {})

    def enforce_constraints(self):
        """Enables immedaite enforcing of deferred constraints.

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

    @cached_property
    def logger(self):
        from indico.core.logger import Logger

        logger = Logger.get('db')
        logger.setLevel(logging.DEBUG)
        return logger

    @contextmanager
    def tmp_session(self):
        """Provides a contextmanager with a temporary SQLAlchemy session.

        This allows you to use SQLAlchemy e.g. in a `after_this_request`
        callback without having to worry about things like the ZODB extension,
        implicit commits, etc.
        """
        session = db.create_session({'query_cls': IndicoBaseQuery})
        try:
            yield session
        except:
            session.rollback()
            raise
        finally:
            session.close()


def on_models_committed(sender, changes):
    for obj, change in changes:
        obj.__committed__(change)


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
    # Create the indico_unaccent function
    create_unaccent_function(connection)


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

db = IndicoSQLAlchemy(session_options={'query_cls': IndicoBaseQuery})
db.Model.metadata.naming_convention = naming_convention
listen(db.Model.metadata, 'before_create', _before_create)
listen(mapper, 'mapper_configured', _mapper_configured)
