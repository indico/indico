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

from __future__ import print_function, unicode_literals

import os
import sys
import time
from operator import itemgetter
from pkg_resources import iter_entry_points

import click
import pytz
from sqlalchemy.sql import func, select

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.logging import apply_db_loggers
from indico.core.db.sqlalchemy.migration import migrate as alembic_migrate
from indico.core.db.sqlalchemy.util.models import import_all_models
from indico.core.plugins import plugin_engine
from indico.modules.users.models.users import User
from indico.util.console import cformat, clear_line
from indico.util.decorators import classproperty
from indico.web.flask.stats import request_stats_request_started, setup_request_stats
from indico.web.flask.wrappers import IndicoFlask
from indico_zodbimport.util import UnbreakingDB, get_storage, patch_makac

click.disable_unicode_literals_warning = True


@click.group()
@click.argument('sqlalchemy-uri')
@click.argument('zodb-uri')
@click.pass_context
def cli(ctx, **kwargs):
    """
    This script migrates data from ZODB to PostgreSQL.

    You always need to specify both the SQLAlchemy connection URI and
    ZODB URI (both zeo:// and file:// work).
    """
    ctx.obj = kwargs
    patch_makac()


class Importer(object):
    #: Specify plugins that need to be loaded for the import (e.g. to access its .settings property)
    plugins = frozenset()

    def __init__(self, sqlalchemy_uri, zodb_uri, quiet, dblog):
        self.sqlalchemy_uri = sqlalchemy_uri
        self.zodb_uri = zodb_uri
        self.quiet = quiet
        self.dblog = dblog
        self.zodb_root = None
        self.app = None
        self.tz = None

    @classproperty
    @classmethod
    def command(cls):
        @click.command()
        @click.option('--quiet', '-q', is_flag=True, default=False, help="Use less verbose/spammy output")
        @click.option('--dblog', '-L', is_flag=True, default=False, help="Enable db query logging")
        @click.pass_obj
        def _command(obj, **kwargs):
            cls(**dict(obj, **kwargs)).run()

        return cls.decorate_command(_command)

    @staticmethod
    def decorate_command(command):
        return command

    def __repr__(self):
        return '<{}({}, {})>'.format(type(self).__name__, self.sqlalchemy_uri, self.zodb_uri)

    def run(self):
        self.setup()
        start = time.time()
        with self.app.app_context():
            self.migrate()
        print('migration took {:.06f} seconds\a'.format((time.time() - start)))

    def setup(self):
        self.app = app = IndicoFlask('indico_zodbimport')
        app.config['PLUGINENGINE_NAMESPACE'] = 'indico.plugins'
        app.config['PLUGINENGINE_PLUGINS'] = self.plugins
        app.config['SQLALCHEMY_DATABASE_URI'] = self.sqlalchemy_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
        plugin_engine.init_app(app)
        if not plugin_engine.load_plugins(app):
            print(cformat('%{red!}Could not load some plugins: {}%{reset}').format(
                ', '.join(plugin_engine.get_failed_plugins(app))))
            sys.exit(1)
        db.init_app(app)
        setup_request_stats(app)
        if self.dblog:
            app.debug = True
            apply_db_loggers(app)
        import_all_models()
        alembic_migrate.init_app(app, db, os.path.join(app.root_path, 'migrations'))

        self.connect_zodb()

        try:
            self.tz = pytz.timezone(getattr(self.zodb_root['MaKaCInfo']['main'], '_timezone', 'UTC'))
        except KeyError:
            self.tz = pytz.utc

        with app.app_context():
            request_stats_request_started()

            if not self.pre_check():
                sys.exit(1)

            if self.has_data():
                # Usually there's no good reason to migrate with data in the DB. However, during development one might
                # comment out some migration tasks and run the migration anyway.
                print(cformat('%{yellow!}*** WARNING'))
                print(cformat('%{yellow!}***%{reset} Your database is not empty, migration may fail or add duplicate '
                              'data!'))
                if raw_input(cformat('%{yellow!}***%{reset} To confirm this, enter %{yellow!}YES%{reset}: ')) != 'YES':
                    print('Aborting')
                    sys.exit(1)

    def connect_zodb(self):
        self.zodb_root = UnbreakingDB(get_storage(self.zodb_uri)).open().root()

    def flushing_iterator(self, iterable, n=5000):
        """Iterates over `iterable` and flushes the ZODB cache every `n` items.

        :param iterable: an iterable object
        :param n: number of items to flush after
        """
        conn = self.zodb_root._p_jar
        for i, item in enumerate(iterable, 1):
            yield item
            if i % n == 0:
                conn.sync()

    def check_plugin_schema(self, name):
        """Checks if a plugin schema exists in the database.

        :param name: Name of the plugin
        """
        sql = 'SELECT COUNT(*) FROM "information_schema"."schemata" WHERE "schema_name" = :name'
        count = db.engine.execute(db.text(sql), name='plugin_{}'.format(name)).scalar()
        if not count:
            print(cformat('%{red!}Plugin schema does not exist%{reset}'))
            print(cformat('Run %{yellow!}indico db --plugin {} upgrade%{reset} to create it').format(name))
            return False
        return True

    def pre_check(self):
        """Early checks before doing anything.

        Add checks here that should run before performing any
        modifications. You could use this method to check if
        the database contains the necessary tables.

        :return: bool indicating if the migration should run
        """
        return True

    def has_data(self):
        return False

    def migrate(self):
        raise NotImplementedError

    def update_merged_users(self, db_column, msg_in):
        self.print_step("Updating merged users in {}".format(msg_in))
        for obj in db_column.class_.find(User.merged_into_id != None, _join=db_column):  # noqa
            initial_user = getattr(obj, db_column.key)
            while getattr(obj, db_column.key).merged_into_user:
                merged_into_user = getattr(obj, db_column.key).merged_into_user
                setattr(obj, db_column.key, merged_into_user)
            msg = cformat('%{cyan}{}%{reset} -> %{cyan}{}%{reset}').format(initial_user, getattr(obj, db_column.key))
            self.print_success(msg, always=True)
        db.session.commit()

    def fix_sequences(self, schema=None, tables=None):
        for name, cls in sorted(db.Model._decl_class_registry.iteritems(), key=itemgetter(0)):
            table = getattr(cls, '__table__', None)
            if table is None:
                continue
            elif schema is not None and table.schema != schema:
                continue
            elif tables is not None and cls.__tablename__ not in tables:
                continue
            # Check if we have a single autoincrementing primary key
            candidates = [col for col in table.c if col.autoincrement and col.primary_key]
            if len(candidates) != 1 or not isinstance(candidates[0].type, db.Integer):
                continue
            serial_col = candidates[0]
            sequence_name = '{}.{}_{}_seq'.format(table.schema, cls.__tablename__, serial_col.name)

            query = select([func.setval(sequence_name, func.max(serial_col) + 1)], table)
            db.session.execute(query)
        db.session.commit()

    def print_msg(self, msg, always=False):
        """Prints a message to the console.

        By default, messages are not shown in quiet mode, but this
        can be changed using the `always` parameter.
        """
        if self.quiet:
            if not always:
                return
            clear_line()
        print(msg)

    def print_step(self, msg):
        """Prints a message about a migration step to the console

        This message is always shown, even in quiet mode.
        """
        self.print_msg(cformat('%{white!}{}%{reset}').format(msg), True)

    def print_prefixed(self, prefix, prefix_color, msg, always=False, event_id=None):
        """Prints a prefixed message to the console."""
        parts = [
            cformat('%%{%s}{}%%{reset}' % prefix_color).format(prefix),
            cformat('%{white!}{:>6s}%{reset}').format(unicode(event_id)) if event_id is not None else None,
            msg
        ]
        self.print_msg(' '.join(filter(None, parts)), always)

    def print_info(self, msg, always=False, has_event=True):
        """Prints an info message to the console.

        By default, info messages are not shown in quiet mode.
        They are prefixed with blank spaces to align with other
        messages.

        When calling this in a loop that is invoked a lot, it is
        recommended to add an explicit ``if not self.quiet`` check
        to avoid expensive `cformat` or `format` calls for a message
        that is never displayed.
        """
        self.print_msg(' ' * (11 if has_event else 4) + msg, always)

    def print_success(self, msg, always=False, event_id=None):
        """Prints a success message to the console.

        By default, success messages are not shown in quiet mode.
        They are prefixed with three green plus signs.

        When calling this in a loop that is invoked a lot, it is
        recommended to add an explicit ``if not self.quiet`` check
        to avoid expensive `cformat` or `format` calls for a message
        that is never displayed.
        """
        self.print_prefixed('+++', 'green', msg, always, event_id)

    def print_warning(self, msg, always=True, event_id=None):
        """Prints a warning message to the console.

        By default, warnings are displayed even in quiet mode.
        Warning messages are with three yellow exclamation marks.
        """
        self.print_prefixed('!!!', 'yellow!', msg, always, event_id)

    def print_error(self, msg, event_id=None):
        """Prints an error message to the console

        Errors are always displayed, even in quiet mode.
        They are prefixed with three red exclamation marks.
        """
        self.print_prefixed('!!!', 'red!', msg, True, event_id)


def main():
    for ep in iter_entry_points('indico.zodb_importers'):
        cli.add_command(ep.load().command, name=ep.name)
    return cli()
