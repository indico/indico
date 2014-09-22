# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

import re

from flask.ext.sqlalchemy import Model, connection_stack
from sqlalchemy import MetaData, ForeignKeyConstraint, Table
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import joinedload, joinedload_all
from sqlalchemy.sql.ddl import DropConstraint, DropTable, DropSchema


TS_REGEX = re.compile(r'([@<>!()&|])')


class IndicoModel(Model):
    """Indico DB model"""

    @classmethod
    def find(cls, *args, **kwargs):
        special_field_names = ('join', 'eager', 'eager_all')
        special_fields = {}
        for key in special_field_names:
            value = kwargs.pop('_{}'.format(key), ())
            if not isinstance(value, (list, tuple)):
                value = (value,)
            special_fields[key] = value
        options = []
        options += [joinedload(rel) for rel in special_fields['eager']]
        options += [joinedload_all(rel) for rel in special_fields['eager_all']]
        return cls.query \
                  .filter_by(**kwargs) \
                  .join(*special_fields['join']) \
                  .filter(*args) \
                  .options(*options)

    @classmethod
    def find_all(cls, *args, **kwargs):
        return cls.find(*args, **kwargs).all()

    @classmethod
    def find_first(cls, *args, **kwargs):
        return cls.find(*args, **kwargs).first()

    @classmethod
    def find_one(cls, *args, **kwargs):
        return cls.find(*args, **kwargs).one()

    @classmethod
    def get(cls, oid):
        return cls.query.get(oid)

    def __committed__(self, change):
        """Called after a commit for this object.

        ALWAYS call super if you override this method!

        :param change: The operation that has been committed (delete/change/update)
        """
        pass


def update_session_options(db, session_options=None):
    """Replaces the Flask-SQLAlchemy session a new one using the given options.

    This can be used when you want a session that does not use the ZopeTransaction extension.
    """
    if session_options is None:
        session_options = {}
    session_options.setdefault(
        'scopefunc', connection_stack.__ident_func__
    )
    db.session = db.create_scoped_session(session_options)


def get_all_tables(db):
    """Returns a dict containing all tables grouped by schema"""
    inspector = Inspector.from_engine(db.engine)
    schemas = sorted(set(inspector.get_schema_names()) - {'information_schema'})
    return dict(zip(schemas, (inspector.get_table_names(schema=schema) for schema in schemas)))


def delete_all_tables(db):
    conn = db.engine.connect()
    transaction = conn.begin()
    inspector = Inspector.from_engine(db.engine)
    metadata = MetaData()

    all_schema_tables = get_all_tables(db)
    tables = []
    all_fkeys = []
    for schema, schema_tables in all_schema_tables.iteritems():
        for table_name in schema_tables:
            fkeys = [ForeignKeyConstraint((), (), name=fk['name'])
                     for fk in inspector.get_foreign_keys(table_name, schema=schema)
                     if fk['name']]
            tables.append(Table(table_name, metadata, *fkeys, schema=schema))
            all_fkeys.extend(fkeys)

    for fkey in all_fkeys:
        conn.execute(DropConstraint(fkey))
    for table in tables:
        conn.execute(DropTable(table))
    for schema in all_schema_tables:
        if schema != 'public':
            conn.execute(DropSchema(schema))
    transaction.commit()


def preprocess_ts_string(text, prefix=True):
    atoms = [TS_REGEX.sub(r'\\\1', atom.strip()) for atom in text.split()]
    return ' & '.join('{}:*'.format(atom) if prefix else atom for atom in atoms)
