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

from sqlalchemy import MetaData, ForeignKeyConstraint, Table
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.sql.ddl import DropConstraint, DropTable, DropSchema

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.util.console import cformat


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
            row = conn.execute("""
                SELECT 'DROP FUNCTION ' || ns.nspname || '.' || proname || '(' || oidvectortypes(proargtypes) || ')'
                FROM pg_proc INNER JOIN pg_namespace ns ON (pg_proc.pronamespace = ns.oid)
                WHERE ns.nspname = '{}'  order by proname;
            """.format(schema))
            for stmt, in row:
                conn.execute(stmt)
            conn.execute(DropSchema(schema))
    transaction.commit()


def create_all_tables(db, verbose=False, add_initial_data=True):
    """Create all tables and required initial objects"""
    from indico.modules.categories import Category
    from indico.modules.users import User
    if verbose:
        print cformat('%{green}Creating tables')
    db.create_all()
    if add_initial_data:
        if verbose:
            print cformat('%{green}Creating system user')
        db.session.add(User(id=0, is_system=True, first_name='Indico', last_name='System'))
        if verbose:
            print cformat('%{green}Creating root category')
        db.session.add(Category(id=0, title='Home', protection_mode=ProtectionMode.public))
        db.session.commit()
