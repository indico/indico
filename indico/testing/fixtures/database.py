# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import re
import shutil
import signal
import subprocess
import tempfile
from contextlib import contextmanager

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine

from indico.core.db import db as db_
from indico.core.db.sqlalchemy.util.management import create_all_tables, delete_all_tables
from indico.util.process import silent_check_call
from indico.web.flask.app import configure_db


@pytest.fixture(scope='session')
def postgresql():
    """Provide a clean temporary PostgreSQL server/database.

    If the environment variable `INDICO_TEST_DATABASE_URI` is set, this fixture
    will do nothing and simply return the connection string from that variable
    """

    # Use existing database
    if 'INDICO_TEST_DATABASE_URI' in os.environ:
        yield os.environ['INDICO_TEST_DATABASE_URI']
        return

    db_name = 'test'

    # Ensure we have initdb and a recent enough postgres version
    try:
        version_output = subprocess.check_output(['initdb', '--version'])
    except Exception as e:
        pytest.skip('Could not retrieve PostgreSQL version: {}'.format(e))
    pg_version = map(int, re.match(r'initdb \(PostgreSQL\) ((?:\d+\.?)+)', version_output).group(1).split('.'))
    if pg_version[0] < 9 or (pg_version[0] == 9 and pg_version[1] < 6):
        pytest.skip('PostgreSQL version is too old: {}'.format(version_output))

    # Prepare server instance and a test database
    temp_dir = tempfile.mkdtemp(prefix='indicotestpg.')
    postgres_args = '-h "" -k "{}"'.format(temp_dir)
    try:
        silent_check_call(['initdb', '--encoding', 'UTF8', temp_dir])
        silent_check_call(['pg_ctl', '-D', temp_dir, '-w', '-o', postgres_args, 'start'])
        silent_check_call(['createdb', '-h', temp_dir, db_name])
        silent_check_call(['psql', '-h', temp_dir, db_name, '-c', 'CREATE EXTENSION unaccent;'])
        silent_check_call(['psql', '-h', temp_dir, db_name, '-c', 'CREATE EXTENSION pg_trgm;'])
    except Exception as e:
        shutil.rmtree(temp_dir)
        pytest.skip('Could not init/start PostgreSQL: {}'.format(e))

    yield 'postgresql:///{}?host={}'.format(db_name, temp_dir)

    try:
        silent_check_call(['pg_ctl', '-D', temp_dir, '-m', 'immediate', 'stop'])
    except Exception as e:
        # If it failed for any reason, try killing it
        try:
            with open(os.path.join(temp_dir, 'postmaster.pid')) as f:
                pid = int(f.readline().strip())
                os.kill(pid, signal.SIGKILL)
            pytest.skip('Could not stop postgresql; killed it instead: {}'.format(e))
        except Exception as e:
            pytest.skip('Could not stop/kill postgresql: {}'.format(e))
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture(scope='session')
def database(app, postgresql):
    """Create a test database which is destroyed afterwards.

    Used only internally, if you need to access the database use `db` instead to ensure
    your modifications are not persistent!
    """
    app.config['SQLALCHEMY_DATABASE_URI'] = postgresql
    configure_db(app)
    if 'INDICO_TEST_DATABASE_URI' in os.environ and os.environ.get('INDICO_TEST_DATABASE_HAS_TABLES') == '1':
        yield db_
        return
    with app.app_context():
        create_all_tables(db_)
    yield db_
    db_.session.remove()
    with app.app_context():
        delete_all_tables(db_)


@pytest.fixture
def db(database, monkeypatch):
    """Provide database access and ensure changes do not persist."""
    # Prevent database/session modifications
    monkeypatch.setattr(database.session, 'commit', database.session.flush)
    monkeypatch.setattr(database.session, 'remove', lambda: None)

    @contextmanager
    def _tmp_session():
        _old_commit = database.session.commit
        database.session.commit = lambda: None
        yield database.session
        database.session.commit = _old_commit

    monkeypatch.setattr(database, 'tmp_session', _tmp_session, lambda: None)
    yield database
    database.session.rollback()
    database.session.remove()


@pytest.fixture
@pytest.mark.usefixtures('db')
def count_queries():
    """Provide a query counter.

    Usage::

        with count_queries() as count:
            do_stuff()
        assert count() == number_of_queries
    """
    def _after_cursor_execute(*args, **kwargs):
        if active_counter[0]:
            active_counter[0][0] += 1

    @contextmanager
    def _counter():
        if active_counter[0]:
            raise RuntimeError('Cannot nest count_queries calls')
        active_counter[0] = counter = [0]
        try:
            yield lambda: counter[0]
        finally:
            active_counter[0] = None

    active_counter = [None]
    event.listen(Engine, 'after_cursor_execute', _after_cursor_execute)
    try:
        yield _counter
    finally:
        event.remove(Engine, 'after_cursor_execute', _after_cursor_execute)
