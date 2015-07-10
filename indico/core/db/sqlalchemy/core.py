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

from __future__ import absolute_import

from contextlib import contextmanager

import logging
from functools import partial
from flask import has_app_context, g, has_request_context
from flask import session as flask_session

import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.event import listen
from sqlalchemy.orm import mapper, Session, CompositeProperty
from sqlalchemy.sql.ddl import CreateSchema
from werkzeug.utils import cached_property
from zope.sqlalchemy import ZopeTransactionExtension

from indico.core.db.sqlalchemy.custom.unaccent import create_unaccent_function

# Monkeypatching this since Flask-SQLAlchemy doesn't let us override the model class
from indico.core.db.sqlalchemy.util.models import IndicoModel
flask_sqlalchemy.Model = IndicoModel


class IndicoSQLAlchemy(SQLAlchemy):
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
        session = db.create_session({})
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


def _should_create_schema(ddl, target, connection, **kw):
    sql = 'SELECT COUNT(*) FROM "information_schema"."schemata" WHERE "schema_name" = :name'
    count = connection.execute(db.text(sql), name=ddl.element).scalar()
    return not count


def _before_create(target, connection, **kw):
    # SQLAlchemy doesn't create schemas so we need to take care of it...
    schemas = {table.schema for table in kw['tables']}
    for schema in schemas:
        CreateSchema(schema).execute_if(callable_=_should_create_schema).execute(connection)
    # Create the indico_unaccent function
    create_unaccent_function(connection)


def _mapper_configured(mapper, class_):
    # Create a setter listener to coerce attribute values for custom types supporting it
    def _coerce_custom(target, value, oldvalue, initiator, fn):
        return fn(value)

    for prop in mapper.iterate_properties:
        if hasattr(prop, 'columns') and not isinstance(prop, CompositeProperty):
            func = getattr(prop.columns[0].type, 'coerce_set_value', None)
            if func is not None:
                # Using partial here to avoid closure scoping issues
                listen(getattr(class_, prop.key), 'set', partial(_coerce_custom, fn=func), retval=True)


def _transaction_ended(session, transaction):
    # The zope transaction system closes the session (and thus the
    # transaction) e.g. when calling `transaction.abort()`.
    # in this case we need to clear the memoization cache to avoid
    # accessing memoized objects (which are now session-less)
    if has_app_context():
        if 'memoize_cache' in g:
            del g.memoize_cache
        if 'settings_cache' in g:
            del g.settings_cache
        if 'event_notes' in g:
            del g.event_notes
        if 'event_attachments' in g:
            del g.event_attachments
    if has_request_context() and hasattr(flask_session, '_user'):
        delattr(flask_session, '_user')


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

db = IndicoSQLAlchemy(session_options={'extension': ZopeTransactionExtension()})
db.Model.metadata.naming_convention = naming_convention
listen(db.Model.metadata, 'before_create', _before_create)
listen(mapper, 'mapper_configured', _mapper_configured)
listen(Session, 'after_transaction_end', _transaction_ended)
