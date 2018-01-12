# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from sqlalchemy import ForeignKeyConstraint, MetaData, Table
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.sql.ddl import DropConstraint, DropSchema, DropTable

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.util.console import cformat


DEFAULT_TEMPLATE_DATA = {
    'background_position': 'stretch', 'width': 850, 'height': 1350, 'items': [
        {'font_size': '24pt', 'bold': False, 'color': 'black', 'text': 'Fixed text', 'selected': False,
         'text_align': 'center', 'font_family': 'sans-serif', 'width': 400, 'italic': False, 'y': 190, 'x': 330,
         'height': None, 'type': 'event_title', 'id': 0},
        {'font_size': '15pt', 'bold': False, 'color': 'black', 'text': 'Fixed text', 'selected': False,
         'text_align': 'left', 'font_family': 'sans-serif', 'width': 400, 'italic': False, 'y': 50, 'x': 50,
         'height': None, 'type': 'event_dates', 'id': 1},
        {'font_size': '15pt', 'bold': False, 'color': 'black', 'text': 'Fixed text', 'selected': False,
         'text_align': 'left', 'font_family': 'sans-serif', 'width': 400, 'italic': False, 'y': 350, 'x': 230,
         'height': None, 'type': 'affiliation', 'id': 2},
        {'font_size': '15pt', 'bold': False, 'color': 'black', 'text': 'Fixed text', 'selected': False,
         'text_align': 'left', 'font_family': 'sans-serif', 'width': 400, 'italic': False, 'y': 310, 'x': 230,
         'height': None, 'type': 'full_name_b', 'id': 3},
        {'font_size': '13.5pt', 'bold': False, 'color': 'black', 'text': 'Fixed text', 'selected': True,
         'text_align': 'left', 'font_family': 'sans-serif', 'width': 400, 'italic': False, 'y': 130, 'x': 50,
         'height': None, 'type': 'event_venue', 'id': 4},
        {'font_size': '15pt', 'bold': False, 'color': 'black', 'text': 'Fixed text', 'selected': False,
         'text_align': 'center', 'font_family': 'sans-serif', 'width': 150, 'italic': False, 'y': 270, 'x': 50,
         'height': 150, 'type': 'ticket_qr_code', 'id': 5},
        {'font_size': '13.5pt', 'bold': False, 'color': 'black', 'text': 'Fixed text', 'selected': False,
         'text_align': 'left', 'font_family': 'sans-serif', 'width': 400, 'italic': False, 'y': 90, 'x': 50,
         'height': None, 'type': 'event_room', 'id': 6}]
}


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
    from indico.modules.designer import TemplateType
    from indico.modules.designer.models.templates import DesignerTemplate
    from indico.modules.oauth.models.applications import OAuthApplication, SystemAppType
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
        cat = Category(id=0, title='Home', protection_mode=ProtectionMode.public)
        db.session.add(cat)
        db.session.flush()
        if verbose:
            print cformat('%{green}Creating default ticket template for root category ')
        dt = DesignerTemplate(category_id=0, title='Default ticket', type=TemplateType.badge,
                              data=DEFAULT_TEMPLATE_DATA, is_system_template=True)
        cat.default_ticket_template = dt
        db.session.add(dt)
        if verbose:
            print cformat('%{green}Creating system oauth apps')
        for sat in SystemAppType:
            if sat != SystemAppType.none:
                db.session.add(OAuthApplication(system_app_type=sat, **sat.default_data))
        db.session.commit()
