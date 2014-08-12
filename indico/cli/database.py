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


from flask_migrate import MigrateCommand as DatabaseManager
from flask_migrate import stamp

from indico.core.db import db
from indico.core.db.sqlalchemy.util import get_all_tables
from indico.util.console import colored, cformat


@DatabaseManager.command
def prepare():
    """Initializes an empty database (creates tables, sets alembic rev to HEAD)"""
    tables = get_all_tables(db)
    if 'alembic_version' not in tables['public']:
        print colored('Setting the alembic version to HEAD', 'green')
        stamp()
        # Retrieve the table list again, that way we fail if the alembic version table was not created
        tables = get_all_tables(db)
    tables['public'].remove('alembic_version')
    if any(tables.viewvalues()):
        print colored('Your database is not empty!', 'red')
        print colored('If you just added a new table/model, create an alembic revision instead!', 'yellow')
        print
        print 'Tables in your database:'
        for schema, schema_tables in sorted(tables.items()):
            for t in schema_tables:
                print cformat('  * %{cyan}{}%{reset}.%{cyan!}{}%{reset}').format(schema, t)
        return
    print colored('Creating tables', 'green')
    db.create_all()
