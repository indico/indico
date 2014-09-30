# This file is part of Indico.
# Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
import time
import sys
from operator import itemgetter
from pkg_resources import iter_entry_points

import click
import pytz
from flask import Flask
from flask_migrate import stamp
from sqlalchemy.sql import func, select

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.migration import migrate as alembic_migrate
from indico.core.db.sqlalchemy.util.management import delete_all_tables
from indico.core.db.sqlalchemy.util.session import update_session_options
from indico.util.console import cformat
from indico.util.decorators import classproperty
from indico_zodbimport.util import UnbreakingDB, get_storage


@click.group()
@click.argument('sqlalchemy-uri')
@click.argument('zodb-uri')
@click.option('--destructive', '-d', is_flag=True, help="delete all existing tables first")
@click.pass_context
def cli(ctx, **kwargs):
    """
    This script migrates data from ZODB to PostgreSQL.

    You always need to specify both the SQLAlchemy connection URI and
    ZODB URI (both zeo:// and file:// work).
    """
    ctx.obj = kwargs


class Importer(object):
    def __init__(self, sqlalchemy_uri, zodb_uri, destructive):
        self.sqlalchemy_uri = sqlalchemy_uri
        self.zodb_uri = zodb_uri
        self.destructive = destructive
        self.zodb_root = None
        self.app = None
        self.tz = None

    @classproperty
    @classmethod
    def command(cls):
        @click.command()
        @click.pass_obj
        def _command(obj, **kwargs):
            cls(**dict(obj, **kwargs)).run()

        return cls.decorate_command(_command)

    @staticmethod
    def decorate_command(command):
        return command

    def __repr__(self):
        return '<{}({}, {}, {})>'.format(type(self).__name__, self.sqlalchemy_uri, self.zodb_uri)

    def run(self):
        self.setup()
        start = time.clock()
        with self.app.app_context():
            self.migrate()
        print 'migration took {:.06f} seconds'.format((time.clock() - start))

    def setup(self):
        update_session_options(db)  # get rid of the zope transaction extension

        self.app = app = Flask('indico_zodbimport')
        app.config['SQLALCHEMY_DATABASE_URI'] = self.sqlalchemy_uri
        db.init_app(app)
        alembic_migrate.init_app(app, db, os.path.join(app.root_path, '..', 'migrations'))

        self.connect_zodb()

        try:
            self.tz = pytz.timezone(getattr(self.zodb_root['MaKaCInfo']['main'], '_timezone', 'UTC'))
        except KeyError:
            self.tz = pytz.utc

        with app.app_context():
            if self.destructive:
                print cformat('%{yellow!}*** DANGER')
                print cformat('%{yellow!}***%{reset} '
                              '%{red!}ALL DATA%{reset} in your database %{yellow!}{!r}%{reset} will be '
                              '%{red!}PERMANENTLY ERASED%{reset}!').format(db.engine.url)
                if raw_input(cformat('%{yellow!}***%{reset} To confirm this, enter %{yellow!}YES%{reset}: ')) != 'YES':
                    print 'Aborting'
                    sys.exit(1)
                delete_all_tables(db)
            stamp()
            db.create_all()
            if self.has_data():
                # Usually there's no good reason to migrate with data in the DB. However, during development one might
                # comment out some migration tasks and run the migration anyway.
                print cformat('%{yellow!}*** WARNING')
                print cformat('%{yellow!}***%{reset} Your database is not empty, migration will most likely fail!')
                if raw_input(cformat('%{yellow!}***%{reset} To confirm this, enter %{yellow!}YES%{reset}: ')) != 'YES':
                    print 'Aborting'
                    sys.exit(1)

    def connect_zodb(self):
        self.zodb_root = UnbreakingDB(get_storage(self.zodb_uri)).open().root()

    def has_data(self):
        return False

    def migrate(self):
        raise NotImplementedError

    def fix_sequences(self, schema=None):
        for name, cls in sorted(db.Model._decl_class_registry.iteritems(), key=itemgetter(0)):
            table = getattr(cls, '__table__', None)
            if table is None:
                continue
            elif schema is not None and table.schema != schema:
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


def main():
    for ep in iter_entry_points('indico.zodb_importers'):
        cli.add_command(ep.load().command, name=ep.name)
    return cli()
