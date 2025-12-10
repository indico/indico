# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import re
import subprocess
import sys
import traceback
from contextlib import contextmanager
from os import listdir
from pathlib import Path
from subprocess import PIPE

import alembic
import alembic.config
import click
from alembic.script import ScriptDirectory
from click import ClickException
from flask.helpers import get_root_path
from results.dbdiff import Migration
from sqlalchemy import create_engine, text
from sqlalchemy.sql.ddl import CreateSchema

from indico.core.db.sqlalchemy.custom.array_utils import (create_array_append_function, create_array_is_unique_function,
                                                          create_array_to_string_function)
from indico.core.db.sqlalchemy.custom.unaccent import create_unaccent_function


INDICO_DIR = Path(get_root_path('indico')).parent
DB_NAME = os.environ.get('DB_NAME') or 'indico_dbtest'
DBDIFF_NAME = os.environ.get('DBDIFF_NAME') or 'indico_dbtest_diff'
PG_USER = os.environ.get('PGUSER') or 'indicotest'
ALEMBIC_INI_FILE = 'bin/utils/testenv/test_alembic.ini'

REGEX_REV_FILENAME = re.compile(r'\d{8}_\d{4}_(\S{12})_.*\.py$')
REG_REV_CODE_HASH = re.compile(r'revision\s*=\s*[\'"](\S+)[\'"]')
REG_DOCSTRING_HASH = re.compile(r'Revision\s*ID:\s*(\S+)')
REG_ADD_COLUMN = re.compile(r'op\.add_column\([^\)]*?sa\.Column\((?P<body>.*?)schema', re.DOTALL)
REG_NON_NULLABLE = re.compile(r'nullable\s*=\s*False')
REG_SERVER_DEFAULT = re.compile(r'server_default\s*=')


def _indent(msg, level=4):
    indentation = level * ' '
    return indentation + msg.replace('\n', '\n' + indentation)


@contextmanager
def _chdir(path):
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


def _validate_plugin_dir(ctx, param, plugin_dir: Path):
    if not plugin_dir:
        return None
    if not list(plugin_dir.glob('*/migrations')):
        raise click.BadParameter(f'no migrations folder found in "{plugin_dir}".')
    return plugin_dir


def _get_test_environment(plugin_dir=None):
    # Minimal indico.conf settings
    plugins = [x.parent.name for x in plugin_dir.glob('*/__init__.py')] if plugin_dir else []
    indico_conf = {
        'SECRET_KEY': '*' * 16,
        'BASE_URL': 'http://localhost/',
        'CELERY_BROKER': 'redis://127.0.0.1:6379/0',
        'REDIS_CACHE_URL': 'redis://127.0.0.1:6379/1',
        'DEBUG': True,
        'PLUGINS': plugins,
        'SQLALCHEMY_DATABASE_URI': _build_db_uri(DB_NAME)
    }
    return {
        'INDICO_CONFIG': '/dev/null',
        'INDICO_CONF_OVERRIDE': repr(indico_conf),
        'INDICO_ALWAYS_DOWNGRADE': 'yes'
    }


def _set_alembic_version_test_db_env(plugin):
    os.environ['ALEMBIC_VERSION_TEST_DB'] = f'alembic_version_plugin_{plugin}'


def _remove_alembic_version_test_db_env():
    os.environ.pop('ALEMBIC_VERSION_TEST_DB', None)


def _build_db_uri(dbname):
    pghost = os.environ.get('PGHOST')
    pgport = os.environ.get('PGPORT')
    parts = ['postgresql://']
    parts += [PG_USER, ':@']
    if pghost:
        parts += [pghost]
        if pgport:
            parts += [':', pgport]
    parts += ['/', dbname]
    return ''.join(parts)


@contextmanager
def _connect_dbs():
    db_eng = create_engine(_build_db_uri(DB_NAME))
    dbdiff_eng = create_engine(_build_db_uri(DBDIFF_NAME))
    db_conn = db_eng.connect()
    dbdiff_conn = dbdiff_eng.connect()
    try:
        yield (db_conn, dbdiff_conn)
    finally:
        db_conn.close()
        db_eng.dispose()
        dbdiff_conn.close()
        dbdiff_eng.dispose()


@contextmanager
def _get_db_context(verbose, plugin_dir=None):
    # HACK: This is necessary because results dbdiff fails to properly sort functions when producing SQL diffs.
    #       Remove once this is fixed: https://github.com/djrobstep/migra/issues/196.
    def prepare_diff_db(dbdiff_connection):
        CreateSchema('indico').execute(dbdiff_connection)
        create_unaccent_function(dbdiff_connection)

    try:
        _prepare_dbs(verbose, plugin_dir)
        with _connect_dbs() as (db_conn, dbdiff_conn):
            prepare_diff_db(dbdiff_conn)
            yield (db_conn, dbdiff_conn)
    except Exception as e:
        if verbose:
            click.secho(traceback.format_exc().rstrip(), fg='red')
        raise ClickException(click.style(str(e), fg='red')) from e
    finally:
        _destroy_dbs()


def _prepare_dbs(verbose, plugin_dir=None):
    click.secho('Begin setting up test DBs...', fg='cyan')
    if plugin_dir is not None:
        test_env = _get_test_environment(plugin_dir=plugin_dir)
    else:
        test_env = _get_test_environment()
    try:
        if 'PGUSER' not in os.environ:
            _run(['createuser', PG_USER])
        _run(['createdb', '-O', PG_USER, DB_NAME])
        _run(['createdb', '-O', PG_USER, DBDIFF_NAME])
        _run(['psql', DB_NAME, '-c', 'CREATE EXTENSION unaccent;'])
        _run(['psql', DB_NAME, '-c', 'CREATE EXTENSION pg_trgm;'])
        _run(['psql', DBDIFF_NAME, '-c', 'CREATE EXTENSION unaccent;'])
        _run(['psql', DBDIFF_NAME, '-c', 'CREATE EXTENSION pg_trgm;'])
        _run(['indico', 'db', 'prepare'], env=test_env)
    except Exception as e:
        if verbose:
            click.secho(f'Failed to set up test DBs due to: {e}', fg='red')
        raise RuntimeError('Test DBs could not be initialized') from e
    click.secho('End setting up test DBs...', fg='cyan')


def _destroy_dbs():
    click.secho('Tearing down test DBs...', fg='cyan')
    _drop_db(DB_NAME)
    _drop_db(DBDIFF_NAME)
    if 'PGUSER' not in os.environ:
        _drop_db_user(PG_USER)


def _drop_db(db_name):
    # Check if database exists. Source: https://stackoverflow.com/a/17757560/1901977
    if _run(['psql', 'postgres', '-XtAc', f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"]) == '1':  # noqa: S608
        _run(['dropdb', db_name])


def _drop_db_user(db_user):
    # Check if user exists. Source: https://stackoverflow.com/a/8546783/1901977
    if _run(['psql', 'postgres', '-XtAc', f"SELECT 1 FROM pg_roles WHERE rolname='{db_user}'"]) == '1':  # noqa: S608
        _run(['dropuser', db_user])


def _run(cmd, input_='', env=None):
    kwargs = {}
    if env:
        kwargs['env'] = os.environ | env
    with subprocess.Popen(cmd, **kwargs, stdin=PIPE, stdout=PIPE, stderr=PIPE) as pipes:
        stdout, stderr = pipes.communicate(input=input_)
        if pipes.returncode != 0:
            error = stderr.decode('unicode_escape').strip()
            raise ClickException(error)
        return stdout.decode('unicode_escape').strip()


def _get_migrations_dir(plugin_dir=None):
    if plugin_dir:
        return os.path.join(os.getcwd(), list(plugin_dir.glob('*/migrations'))[0])
    return os.path.join(os.getcwd(), 'indico/migrations/versions')


def _get_alembic_config(db_conn, stdout=sys.stdout, plugin_dir=None):
    """Configure alembic for running against revisions."""
    config = alembic.config.Config(ALEMBIC_INI_FILE, attributes={'connection': db_conn}, stdout=stdout)
    config.set_main_option('script_location', str(INDICO_DIR) + '/bin/utils/testenv')
    config.set_main_option('version_locations', _get_migrations_dir(plugin_dir))
    return config


def _get_revision_filenames(plugin_dir=None):
    migrations_dir = _get_migrations_dir(plugin_dir)
    if plugin_dir:
        return sorted(f for f in listdir(migrations_dir)
                      if REGEX_REV_FILENAME.match(f))
    return sorted(f for f in listdir(migrations_dir) if REGEX_REV_FILENAME.match(f))


def _check_no_unreachable_revisions(migrations, plugin_dir=None):
    """Check that there are no unreachable Alembic revision files.

    Unreachable Alembic revision files are those whose `down_revision` points to
    a revision not in history.
    """
    filenames = _get_revision_filenames(plugin_dir)
    if len(migrations) < len(filenames):
        for filename in filenames[len(migrations):]:
            click.secho(_indent(f'Revision file {filename} is orphaned'), fg='red')
        raise ClickException(click.style('Orphaned revisions found', fg='red'))
    click.secho(_indent('No orphaned revision was found'), fg='green')


def _check_revision_file_order(migrations, nb_scripts=0, plugin_dir=None):
    """Check that the Alembic revision and their files have the same order.

    This uses the Alembic migration history as the canonical order and expects the Alembic
    revision files to be named so that the ascending order matches. If any
    Alembic revision file is out of order, the expected solution is to modify
    the datetime segment of the file name.
    """
    filenames = _get_revision_filenames(plugin_dir)
    if nb_scripts:
        migrations = migrations[-nb_scripts:]
        filenames = filenames[-nb_scripts:]
    for migration, filename in zip(migrations, filenames, strict=True):
        filename_revision = REGEX_REV_FILENAME.findall(filename)[0]
        if migration.revision != filename_revision:
            click.secho(
                _indent(f'Revision {filename_revision} seems out of order. Expected {migration.revision} instead.'),
                fg='red')
            raise ClickException(click.style('Revision files seem out of order.', fg='red'))
    click.secho(_indent('Revision history files are properly sorted'), fg='green')


def _check_correct_revision_hash(content, file_name, file_path):
    """Check that the alembic revision hash in the code matches the one in the docstring."""
    file_name_hash = REGEX_REV_FILENAME.findall(file_name)[0]
    code_hash = REG_REV_CODE_HASH.findall(content)[0]
    docstring_hash = REG_DOCSTRING_HASH.findall(content)[0]
    if file_name_hash != code_hash or docstring_hash != code_hash:
        click.secho(_indent(f'Revision hash does not match the hash in the docstring in {file_path}.'), fg='red')
        raise ClickException(click.style('Mismatch in revision hash found.', fg='red'))


def _check_server_default_in_non_nullable_column(content, file_path):
    """Check that adding non nullable columns to an existing table includes a server default."""
    for match in REG_ADD_COLUMN.finditer(content):
        body = match.group('body')
        if REG_NON_NULLABLE.search(body) and not REG_SERVER_DEFAULT.search(body):
            click.secho(_indent(f'Non nullable column has no server_default set in {file_path}.'), fg='red')
            raise ClickException(click.style('Missing server default in non nullable column.', fg='red'))


def _check_file_content(nb_scripts=0, plugin_dir=None):
    """Check that the content of the revision file is correct."""
    file_names = _get_revision_filenames(plugin_dir)[::-1]
    if nb_scripts:
        file_names = file_names[:nb_scripts]
    for file_name in file_names:
        if plugin_dir:
            file_path = Path(_get_migrations_dir(plugin_dir) + '/' + file_name)
        else:
            file_path = Path(_get_migrations_dir(plugin_dir) + '/' + file_name)
        content = file_path.read_text()
        _check_correct_revision_hash(content, file_name, file_path)
        _check_server_default_in_non_nullable_column(content, file_path)

    click.secho(_indent('Revision hash matches the one in the docstring'), fg='green')
    click.secho(_indent('Server defaults checked'), fg='green')


def _check_history(nb_scripts=0, plugin_dir=None):
    click.secho('Begin checking Alembic revision history consistency:', fg='cyan')
    migrations_dir = os.path.join(os.getcwd(), _get_migrations_dir(plugin_dir))
    script_directory = ScriptDirectory(str(INDICO_DIR) + '/bin/utils/testenv',
                                       version_locations=[migrations_dir])
    # Check single migration head
    heads = script_directory.get_heads()
    if len(heads) != 1:
        for head in heads:
            click.secho(_indent(head), fg='red')
        raise ClickException('More than one revision head found')
    else:
        click.secho(_indent('Revision history has one single head'), fg='green')
    migrations = script_directory.walk_revisions()
    migrations = list(reversed(list(migrations)))
    _check_no_unreachable_revisions(migrations, plugin_dir)
    _check_revision_file_order(migrations, nb_scripts, plugin_dir)
    _check_file_content(nb_scripts, plugin_dir)
    click.secho('End checking Alembic revision history consistency.', fg='cyan')


def _get_db_diff(base_db_conn, target_db_conn):
    """Synchronize a base DB to a target DB and return the diff.

    Takes two SQLAlchemy DB connections to perform the synchronization
    operation using migra.
    """
    migration = Migration(base_db_conn, target_db_conn)
    migration.set_safety(False)
    migration.add_all_changes()
    return migration.sql


def _sync_dbs(base_db_conn, target_db_conn):
    migration = Migration(base_db_conn, target_db_conn)
    migration.set_safety(False)
    migration.add_all_changes()
    diff = migration.sql
    if not diff:
        return
    with base_db_conn.begin():
        base_db_conn.execute(text(diff))


def _check_script_idempotence(db_conn, dbdiff_conn, nb_scripts=0, plugin_dir=None):
    """Check that revisions are idempotent.

    Starting from newest to oldest, applies downgrade+upgrade scripts to
    verify that they leave the database in the same state as it was before.

    :param nb_scripts: Number of migration scripts to check.
    """
    click.secho('Checking Alembic revision scripts correctness (newer to older):')
    config = _get_alembic_config(db_conn, plugin_dir=plugin_dir)
    # XXX: Initialize DB for diff with function that results dbdiff doesn't create in the proper order.
    #      https://github.com/djrobstep/migra/issues/196
    create_array_append_function(dbdiff_conn)
    create_array_is_unique_function(dbdiff_conn)
    create_array_to_string_function(dbdiff_conn)
    migrations_dir = _get_migrations_dir(plugin_dir)
    scripts = ScriptDirectory(str(INDICO_DIR) + '/bin/utils/testenv',
                              version_locations=[migrations_dir]).walk_revisions()
    scripts = list(scripts)[:nb_scripts] if nb_scripts else list(scripts)
    total_scripts = len(scripts)
    for idx, script in enumerate(scripts):
        rev = script.revision
        _sync_dbs(dbdiff_conn, db_conn)
        progress = f'[{idx + 1}/{total_scripts}]'
        try:
            alembic.command.downgrade(config, '-1')
        except Exception:
            click.secho(_indent(f'{progress} Revision {rev} cannot be applied (downgrade)'), fg='red')
            raise
        try:
            alembic.command.upgrade(config, '+1')
        except Exception:
            click.secho(_indent(f'{progress} Revision {rev} cannot be applied (upgrade)'), fg='red')
            raise
        if diff := _get_db_diff(dbdiff_conn, db_conn):
            click.secho(_indent(f'{progress} Revision {rev} is not idempotent'), fg='red')
            raise ClickException(f'Upgrade script in revision {rev} should be applying:\n\n{diff}')
        alembic.command.downgrade(config, '-1')
        click.secho(_indent(f'{progress} Revision {rev} is correct'), fg='green')
    click.secho('All revisions are correct', fg='green')


@click.command()
@click.option('-n', '--nb-scripts', 'nb_scripts', default=0, type=int, show_default=True,
              help='Number of scripts to check from the most recent (0 checks all)')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False, show_default=True,
              help='Print debug information.')
@click.option('-p', '--plugin-dir', 'plugin_dir', help='Path to an indico plugin', required=False,
              type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path),
              callback=_validate_plugin_dir)
def main(nb_scripts, verbose, plugin_dir):
    """Check sanity of Alembic revision history and migration scripts.
    By default, two test databases named 'indico_dbtest' and
    'indico_dbtest_diff' will be created and dropped. The database names will be
    overridden by the DB_NAME and DBDIFF_NAME environment variables.

    Since this script uses the command-line PostgreSQL tools any other
    configuration should be done using the various environment variables like
    PGHOST, PGPORT and PGUSER) and your `.pgpass` file.
    """
    if plugin_dir and not plugin_dir.samefile(os.getcwd()):
        with _chdir(plugin_dir):
            plugin = [x.parent.name for x in plugin_dir.glob('*/__init__.py')]
            assert len(plugin) == 1
            _set_alembic_version_test_db_env(plugin[0])
            click.secho(f'Running db tests for plugin {plugin[0]}', fg='white', bold=True)
            _check_history(nb_scripts, plugin_dir)
            with _get_db_context(verbose, plugin_dir) as (db_conn, dbdiff_conn):
                _check_script_idempotence(db_conn, dbdiff_conn, nb_scripts, plugin_dir)
            _remove_alembic_version_test_db_env()
    else:
        click.secho('Running db tests for Indico', fg='white', bold=True)
        _check_history(nb_scripts)
        # with _get_db_context(verbose) as (db_conn, dbdiff_conn):
        #     _check_script_idempotence(db_conn, dbdiff_conn, nb_scripts)


if __name__ == '__main__':
    main()
