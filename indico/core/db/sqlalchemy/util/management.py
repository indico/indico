# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from sqlalchemy import MetaData, ForeignKeyConstraint, Table
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.sql.ddl import DropConstraint, DropTable, DropSchema


def get_all_tables(db):
    """Returns a dict containing all tables grouped by schema"""
    inspector = Inspector.from_engine(db.engine)
    schemas = sorted(set(inspector.get_schema_names()) - {'information_schema'})
    return dict(zip(schemas, (inspector.get_table_names(schema=schema) for schema in schemas)))


def delete_all_tables(db):
    """Drops all tables in the database"""
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
