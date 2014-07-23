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

from flask_migrate import MigrateCommand
from flask_script import Manager

from indico.cli.shell import IndicoShell
from indico.core.db import db
from indico.core.db.sqlalchemy.migration import migrate
from indico.web.flask.app import make_app


def app_factory():
    app = make_app()
    migrate.init_app(app, db)
    return app


manager = Manager(app_factory, with_default_commands=False)
manager.add_command('shell', IndicoShell())
manager.add_command('db', MigrateCommand)


def main():
    manager.run()
