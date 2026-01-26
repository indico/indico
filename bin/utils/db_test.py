#!/usr/bin/env python
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
ALEMBIC_TESTENV_DIR = INDICO_DIR / 'bin' / 'utils' / 'testenv'
ALEMBIC_INI_FILE = ALEMBIC_TESTENV_DIR / 'test_alembic.ini'

DB_NAME = os.environ.get('DB_NAME') or 'indico_dbtest'
DBDIFF_NAME = os.environ.get('DBDIFF_NAME') or 'indico_dbtest_diff'
PG_USER = os.environ.get('PGUSER') or 'indicotest'

REGEX_REV_FILENAME = re.compile(r'\d{8}_\d{4}_(\S{12})_.*\.py$')
REGEX_REV_CODE_HASH = re.compile(r'revision\s*=\s*[\'"](\S+)[\'"]')
REGEX_DOCSTRING_HASH = re.compile(r'Revision\s*ID:\s*(\S+)')
REGEX_ADD_COLUMN = re.compile(r'op\.add_column\([^\)]*?sa\.Column\((?P<body>.*?)schema', re.DOTALL)
REGEX_NON_NULLABLE = re.compile(r'nullable\s*=\s*False')
REGEX_SERVER_DEFAULT = re.compile(r'server_default\s*=')


# -- Top-level checks --------------------------------------------------------------------------------------------------

def _check(nb_scripts=0, verbose=False, plugin_dir=None):
    _check_history(plugin_dir, verbose)
    _check_contents(plugin_dir, verbose)
    _check_scripts(nb_scripts, plugin_dir, verbose)


def _check_history(plugin_dir=None, verbose=False):
    click.secho('Checking Alembic revision history consistency:')
    migrations_dir = _get_migrations_dir(plugin_dir)
    script_dir = ScriptDirectory(ALEMBIC_TESTENV_DIR, version_locations=[migrations_dir])
    revisions = script_dir.walk_revisions()
    revisions = list(reversed(list(revisions)))
    if verbose:
        click.secho(_indent(f'{len(revisions)} revisions found'), fg='cyan')
    _check_single_revision_head(script_dir)
    _check_no_unreachable_revisions(revisions, plugin_dir)
    _check_revision_file_order(revisions, plugin_dir)


def _check_contents(plugin_dir=None, verbose=False):
    """Check that the content of the revision file is correct."""
    click.secho('Checking Alembic revision contents:')
    file_names = _get_revision_filenames(plugin_dir)[::-1]
    # TODO: Why limit it to nb_scripts? This check is quick anyway.
    # if nb_scripts:
    #     rev_files = rev_files[:nb_scripts]
    if verbose:
        click.secho(_indent(f'{len(file_names)} revision files found'), fg='cyan')
    migrations_dir = _get_migrations_dir(plugin_dir)
    for file_name in file_names:
        file_path = migrations_dir / file_name
        content = file_path.read_text()
        _check_consistent_revision_hash(content, file_name, file_path)
        _check_server_default_in_non_nullable_column(content, file_path)
    click.secho(_indent('Revision hashes are consistent'), fg='green')
    click.secho(_indent('No server defaults missing'), fg='green')


def _check_scripts(nb_scripts=0, plugin_dir=None, verbose=False):
    """Check that revisions are idempotent.

    :param nb_scripts: Number of revision scripts to check.
    """
    click.secho('Checking Alembic revision scripts (newer to older):')
    with _get_db_context(plugin_dir, verbose) as (db_conn, dbdiff_conn):
        config = _get_alembic_config(db_conn, plugin_dir=plugin_dir)
        migrations_dir = _get_migrations_dir(plugin_dir)
        scripts = ScriptDirectory(ALEMBIC_INI_FILE, version_locations=[migrations_dir]).walk_revisions()
        scripts = list(scripts)[:nb_scripts] if nb_scripts else list(scripts)
        _check_script_idempotence(scripts, db_conn, dbdiff_conn, config)


# -- Check history operations ------------------------------------------------------------------------------------------

def _check_single_revision_head(script_dir):
    """Check that the Alembic revision history has a single head."""
    heads = script_dir.get_heads()
    if len(heads) > 1:
        for head in heads:
            click.secho(_indent(head), fg='red')
        raise ClickException('More than one revision head found')
    click.secho(_indent('Revision history has one single head'), fg='green')


def _check_no_unreachable_revisions(migrations, plugin_dir=None):
    """Check that there are no unreachable Alembic revision files.

    Unreachable Alembic revision files are those whose `down_revision` point to
    a revision not in the history.
    """
    filenames = _get_revision_filenames(plugin_dir)
    if len(migrations) < len(filenames):
        for filename in filenames[len(migrations):]:
            click.secho(_indent(f'Revision file {filename} is orphaned'), fg='red')
        raise ClickException(click.style('Orphaned revisions found', fg='red'))
    click.secho(_indent('No orphaned revision was found'), fg='green')


def _check_revision_file_order(migrations, plugin_dir=None):
    """Check that the Alembic revision and their filenames have the same ordering.

    This uses the Alembic migration history as the canonical order and expects the
    Alembic revision files to be named so that the ascending order matches.  If
    any Alembic revision file is out of order, the expected solution is to modify
    the datetime segment of the filename.
    """
    filenames = _get_revision_filenames(plugin_dir)
    # TODO: Why limit it to nb_scripts? This check is quick anyway.
    # if nb_scripts:
    #     migrations = migrations[-nb_scripts:]
    #     filenames = filenames[-nb_scripts:]
    for migration, filename in zip(migrations, filenames, strict=True):
        filename_rev = REGEX_REV_FILENAME.findall(filename)[0]
        if migration.revision != filename_rev:
            click.secho(
                _indent(f'Revision {filename_rev} is out of order. Expected {migration.revision} instead.'), fg='red')
            raise ClickException(click.style('Revision files seem out of order.', fg='red'))
    click.secho(_indent('Revision history files are properly sorted'), fg='green')


# -- Check contents operations -----------------------------------------------------------------------------------------

def _check_consistent_revision_hash(content, file_name, file_path):
    """Check that the alembic revision hash in the code matches the one in the docstring."""
    file_name_hash = REGEX_REV_FILENAME.findall(file_name)[0]
    code_hash = REGEX_REV_CODE_HASH.findall(content)[0]
    docstring_hash = REGEX_DOCSTRING_HASH.findall(content)[0]
    if file_name_hash != code_hash or docstring_hash != code_hash:
        click.secho(_indent(f'Revision hash does not match the hash in the docstring in {file_path}.'), fg='red')
        raise ClickException(click.style('Mismatch in revision hash found.', fg='red'))


def _check_server_default_in_non_nullable_column(content, file_path):
    """Check that adding non-nullable columns to an existing table includes a server default."""
    for match in REGEX_ADD_COLUMN.finditer(content):
        body = match.group('body')
        if REGEX_NON_NULLABLE.search(body) and not REGEX_SERVER_DEFAULT.search(body):
            click.secho(_indent(f'Non-nullable column has no server_default set in {file_path}.'), fg='red')
            raise ClickException(click.style('Missing server default in non-nullable column.', fg='red'))


# -- Check script operations -------------------------------------------------------------------------------------------

def _check_script_idempotence(scripts, db_conn, dbdiff_conn, config):
    """Check that revisions are idempotent.

    Starting from newest to oldest, applies downgrade+upgrade scripts to
    verify that they leave the database in the same state as it was before.
    """
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
    click.secho(_indent('All revisions are correct'), fg='green')


# -- DB context functions ----------------------------------------------------------------------------------------------

@contextmanager
def _get_db_context(plugin_dir=None, verbose=False):
    # XXX: This is necessary because results dbdiff fails to properly sort functions when producing SQL diffs.
    #      Remove once this is fixed: https://github.com/djrobstep/migra/issues/196.
    def prepare_diff_db(dbdiff_connection):
        CreateSchema('indico').execute(dbdiff_connection)
        create_unaccent_function(dbdiff_connection)
        create_array_append_function(dbdiff_conn)
        create_array_is_unique_function(dbdiff_conn)
        create_array_to_string_function(dbdiff_conn)

    try:
        click.secho(_indent('Setting up test DBs...'), fg='cyan')
        _prepare_dbs(plugin_dir, verbose)
        with _connect_dbs() as (db_conn, dbdiff_conn):
            prepare_diff_db(dbdiff_conn)
            yield (db_conn, dbdiff_conn)
    except Exception as e:
        if verbose:
            click.secho(traceback.format_exc().rstrip(), fg='red')
        raise ClickException(click.style(str(e), fg='red')) from e
    finally:
        click.secho(_indent('Tearing down test DBs...'), fg='cyan')
        _destroy_dbs()


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


# -- DB helper functions -----------------------------------------------------------------------------------------------

def _prepare_dbs(plugin_dir=None, verbose=False):
    test_env = _get_test_environment(plugin_dir=plugin_dir)
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
            click.secho(_indent(f'Failed to set up test DBs due to: {e}'), fg='red')
        raise RuntimeError('Test DBs could not be initialized') from e


def _destroy_dbs():
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


def _get_db_diff(base_db_conn, target_db_conn):
    migration = Migration(base_db_conn, target_db_conn)
    migration.set_safety(False)
    migration.add_all_changes()
    return migration.sql


def _sync_dbs(base_db_conn, target_db_conn):
    """Synchronize a base DB to a target DB and return the diff."""
    diff = _get_db_diff(base_db_conn, target_db_conn)
    if not diff:
        return
    with base_db_conn.begin():
        base_db_conn.execute(text(diff))


# -- Alembic helper functions ------------------------------------------------------------------------------------------

def _get_migrations_dir(plugin_dir=None):
    if plugin_dir:
        return next(plugin_dir.glob('*/migrations'))
    # TODO: Should it be possible to specify a runtime directory for Indico core, not just plugins?
    return Path(os.getcwd()) / 'indico' / 'migrations' / 'versions'


def _get_alembic_config(db_conn, stdout=sys.stdout, plugin_dir=None):
    """Configure alembic for running against revisions."""
    config = alembic.config.Config(ALEMBIC_INI_FILE, attributes={'connection': db_conn}, stdout=stdout)
    config.set_main_option('script_location', str(ALEMBIC_TESTENV_DIR))
    config.set_main_option('version_locations', str(_get_migrations_dir(plugin_dir)))
    return config


def _get_revision_filenames(plugin_dir=None):
    migrations_dir = _get_migrations_dir(plugin_dir)
    return sorted(f for f in listdir(migrations_dir) if REGEX_REV_FILENAME.match(f))


# -- Environment helper functions --------------------------------------------------------------------------------------

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


def _set_alembic_version_test_db_env(plugin):
    os.environ['ALEMBIC_VERSION_TEST_DB'] = f'alembic_version_plugin_{plugin}'


# -- helper functions --------------------------------------------------------------------------------------------------

def _indent(msg, level=4):
    indentation = level * ' '
    return indentation + msg.replace('\n', '\n' + indentation)


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


def _validate_plugin_dir(ctx, param, plugin_dir: Path):
    if not plugin_dir:
        return None
    if not list(plugin_dir.glob('*/migrations')):
        raise click.BadParameter(f'no migrations folder found in "{plugin_dir}".')
    return plugin_dir


# -- Entrypoint --------------------------------------------------------------------------------------------------------

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
    if not plugin_dir:
        click.secho('Running DB checks for Indico', fg='cyan', bold=True)
        _check(nb_scripts, verbose)
    else:
        os.chdir(plugin_dir)
        plugin_name = next((x.parent.name for x in plugin_dir.glob('*/__init__.py')), None)
        if not plugin_name:
            raise ClickException(click.style('Expected exactly one plugin in plugin dir', fg='red'))
        _set_alembic_version_test_db_env(plugin_name)
        click.secho(f'Running DB checks for plugin "{plugin_name}"', fg='cyan', bold=True)
        _check(nb_scripts, verbose, plugin_dir)


if __name__ == '__main__':
    main()
