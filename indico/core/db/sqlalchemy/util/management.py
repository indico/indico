# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import click
from sqlalchemy import ForeignKeyConstraint, MetaData, Table, inspect
from sqlalchemy.sql.ddl import DropConstraint, DropSchema, DropTable

from indico.core.db.sqlalchemy.protection import ProtectionMode


DEFAULT_TICKET_DATA = {
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

DEFAULT_BADGE_DATA = {
    'background_position': 'stretch', 'width': 425, 'height': 270, 'items': [
        {'font_family': 'sans-serif', 'font_size': '10pt', 'bold': False, 'color': 'black', 'text': 'Fixed text',
         'selected': False, 'text_align': 'right', 'height': None, 'width': 275, 'italic': False, 'y': 42, 'x': 129,
         'type': 'event_title', 'id': 0},
        {'font_family': 'sans-serif', 'font_size': '7pt', 'bold': False, 'color': 'black', 'text': 'Fixed text',
         'selected': False, 'text_align': 'right', 'height': None, 'width': 275, 'italic': False, 'y': 85, 'x': 128,
         'type': 'event_dates', 'id': 1},
        {'font_family': 'sans-serif', 'font_size': '10pt', 'bold': False, 'color': 'black', 'text': 'Fixed text',
         'selected': False, 'text_align': 'left', 'height': None, 'width': 385, 'italic': False, 'y': 168, 'x': 20,
         'type': 'affiliation', 'id': 2},
        {'font_family': 'sans-serif', 'font_size': '12pt', 'bold': True, 'color': 'black', 'text': 'Fixed text',
         'selected': False, 'text_align': 'left', 'height': None, 'width': 385, 'italic': False, 'y': 123, 'x': 20,
         'type': 'full_name_b', 'id': 3},
        {'font_family': 'sans-serif', 'font_size': '7.5pt', 'bold': False, 'color': 'black', 'text': 'Fixed text',
         'selected': False, 'text_align': 'left', 'height': None, 'width': 385, 'italic': False, 'y': 194, 'x': 20,
         'type': 'position', 'id': 4},
        {'font_family': 'sans-serif', 'font_size': '7pt', 'bold': False, 'color': 'black', 'text': 'Fixed text',
         'selected': False, 'text_align': 'left', 'height': None, 'width': 385, 'italic': False, 'y': 218, 'x': 20,
         'type': 'country', 'id': 5}]
}


def get_all_tables(db):
    """Return a dict containing all tables grouped by schema."""
    inspector = inspect(db.engine)
    schemas = sorted(set(inspector.get_schema_names()) - {'information_schema'})
    return dict(zip(schemas, (inspector.get_table_names(schema=schema) for schema in schemas), strict=True))


def delete_all_tables(db):
    """Drop all tables in the database."""
    conn = db.engine.connect()
    transaction = conn.begin()
    inspector = inspect(db.engine)
    metadata = MetaData()

    all_schema_tables = get_all_tables(db)
    tables = []
    all_fkeys = []
    for schema, schema_tables in all_schema_tables.items():
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
            row = conn.execute(f'''
                SELECT 'DROP FUNCTION ' || ns.nspname || '.' || proname || '(' || oidvectortypes(proargtypes) || ')'
                FROM pg_proc INNER JOIN pg_namespace ns ON (pg_proc.pronamespace = ns.oid)
                WHERE ns.nspname = '{schema}' order by proname;
            ''')  # noqa: S608
            for stmt, in row:
                conn.execute(stmt)
            conn.execute(DropSchema(schema))
    transaction.commit()


def create_all_tables(db, verbose=False, add_initial_data=True):
    """Create all tables and required initial objects."""
    from indico.core.oauth.models.applications import OAuthApplication, SystemAppType
    from indico.modules.categories import Category
    from indico.modules.categories.models.categories import InheritableConfigMode
    from indico.modules.designer import TemplateType
    from indico.modules.designer.models.templates import DesignerTemplate
    from indico.modules.users import User
    if verbose:
        click.secho('Creating tables', fg='green')
    db.create_all()
    if add_initial_data:
        if verbose:
            click.secho('Creating system user', fg='green')
        db.session.add(User(id=0, is_system=True, first_name='Indico', last_name='System'))
        if verbose:
            click.secho('Creating root category', fg='green')
        cat = Category(id=0, title='Home', protection_mode=ProtectionMode.public,
                       google_wallet_mode=InheritableConfigMode.disabled,
                       apple_wallet_mode=InheritableConfigMode.disabled)
        db.session.add(cat)
        db.session.flush()
        if verbose:
            click.secho('Creating default ticket template for root category', fg='green')
        dtt = DesignerTemplate(category_id=0, title='Default ticket', type=TemplateType.badge,
                               data=DEFAULT_TICKET_DATA, is_system_template=True)
        dbt = DesignerTemplate(category_id=0, title='Default badge', type=TemplateType.badge,
                               data=DEFAULT_BADGE_DATA, is_system_template=True)
        cat.default_ticket_template = dtt
        cat.default_badge_template = dbt
        db.session.add(dtt)
        db.session.add(dbt)
        if verbose:
            click.secho('Creating system oauth apps', fg='green')
        for sat in SystemAppType:
            if sat != SystemAppType.none:
                db.session.add(OAuthApplication(system_app_type=sat, **sat.default_data))
        db.session.commit()
