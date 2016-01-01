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

import os
import sys

from flask_script import Manager

from indico.cli.admin import IndicoAdminManager
from indico.cli.database import DatabaseManager, PluginDatabaseManager
from indico.cli.server import IndicoDevServer
from indico.cli.shell import IndicoShell
from indico.cli.i18n import IndicoI18nManager
from indico.core import signals
from indico.core.celery.cli import IndicoCeleryCommand
from indico.core.db import db
from indico.core.db.sqlalchemy.migration import migrate
from indico.web.flask.app import make_app


def main():
    app = make_app(set_path=True)
    migrate.init_app(app, db, os.path.join(app.root_path, '..', 'migrations'))
    manager = Manager(app, with_default_commands=False)

    manager.add_command('shell', IndicoShell())
    manager.add_command('admin', IndicoAdminManager)
    manager.add_command('db', DatabaseManager)
    manager.add_command('plugindb', PluginDatabaseManager)
    manager.add_command('runserver', IndicoDevServer())
    manager.add_command('i18n', IndicoI18nManager)
    manager.add_command('celery', IndicoCeleryCommand)
    signals.plugin.cli.send(manager)

    try:
        manager.run()
    except KeyboardInterrupt:
        print
        sys.exit(1)
