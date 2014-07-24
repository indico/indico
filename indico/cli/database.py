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


from flask_migrate import MigrateCommand as DatabaseManager
from flask_migrate import stamp
from sqlalchemy.engine.reflection import Inspector

from indico.core.db import db
from indico.util.console import colored


@DatabaseManager.command
def prepare():
    """Initializes an empty database (creates tables, sets alembic rev to HEAD)"""
    tables = Inspector.from_engine(db.engine).get_table_names()
    if 'alembic_version' not in tables:
        print colored('Setting the alembic version to HEAD', 'green')
        stamp()
        # Retrieve the table list again, that way we fail if the alembic version table was not created
        tables = Inspector.from_engine(db.engine).get_table_names()
    tables.remove('alembic_version')
    if tables:
        print colored('Your database is not empty!', 'red')
        print colored('If you just added a new table/model, create an alembic revision instead!', 'yellow')
        print
        print 'Tables in your database:'
        for t in sorted(tables):
            print '  * {}'.format(t)
        return
    print colored('Creating tables', 'green')
    db.create_all()
