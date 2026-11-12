#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
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
from pathlib import Path
from subprocess import PIPE

import alembic.command
import alembic.config
import click
from alembic.script import ScriptDirectory
from click import BadParameter, ClickException
from flask.helpers import get_root_path
from results.dbdiff import Migration
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool


INDICO_DIR = Path(get_root_path('indico')).parent
ALEMBIC_TESTENV_DIR = INDICO_DIR / 'bin' / 'utils' / 'testenv'
ALEMBIC_INI_FILE = ALEMBIC_TESTENV_DIR / 'test_alembic.ini'

DB_NAME = os.environ.get('DB_NAME') or 'indico_dbtest'
DBDIFF_NAME = os.environ.get('DBDIFF_NAME') or 'indico_dbtest_diff'
DBCLEAN_NAME = os.environ.get('DBCLEAN_NAME') or 'indico_dbtest_clean'
PG_USER = os.environ.get('PGUSER') or 'indicotest'

REGEX_REV_FILENAME = re.compile(r'\d{8}_\d{4}_(\S{12})_.*\.py$')
REGEX_REV_CODE_HASH = re.compile(r'revision\s*=\s*[\'"](\S+)[\'"]')
REGEX_REV_DOCSTRING_HASH = re.compile(r'Revision\s*ID:\s*(\S+)')
REGEX_ADD_COLUMN = re.compile(r'op\.add_column\([^\)]*?sa\.Column\((?P<body>.*?)schema', re.DOTALL)
REGEX_NON_NULLABLE = re.compile(r'nullable\s*=\s*False')
REGEX_SERVER_DEFAULT = re.compile(r'server_default\s*=')


@click.command()
@click.option('-n', '--nb-scripts', 'nb_scripts', default=0, type=int, show_default=True,
              help='Number of scripts to check from the most recent (0 checks all)')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False, show_default=True,
              help='Print debug information.')
@click.option('-p', '--plugin-dir', 'plugin_dir', help='Path to an indico plugin directory', required=False,
              type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path),
              callback=lambda ctx, param, value: _validate_plugin_dir(ctx, param, value))
def main(nb_scripts, verbose, plugin_dir):
    """Check sanity of Alembic revision history and migration scripts.
    By default, three test databases named 'indico_dbtest',
    'indico_dbtest_diff' and 'indico_dbtest_clean' will be created and dropped.
    The database names will be overridden by the DB_NAME, DBDIFF_NAME and
    DBCLEAN_NAME environment variables.

    Since this script uses the command-line PostgreSQL tools any other
    configuration should be done using the various environment variables like
    PGHOST, PGPORT and PGUSER) and your `.pgpass` file.
    """
    plugin_name = _get_plugin_name(plugin_dir) if plugin_dir else None
    target = 'Indico' if not plugin_name else f'plugin "{plugin_name}"'
    click.secho(f'Running DB checks for {target}', fg='blue', bold=True)
    _set_test_environment(plugin_name, verbose)
    _check(nb_scripts, plugin_dir, verbose)


# -- Validations -------------------------------------------------------------------------------------------------------

def _validate_plugin_dir(ctx, param, plugin_dir: Path):
    if not plugin_dir:
        return None
    if plugin_dir == INDICO_DIR:
        raise BadParameter(click.style(f'\nIndico core found in {plugin_dir}', fg='red'))
    try:
        plugin_name = _get_plugin_name(plugin_dir)
    except ClickException as e:
        raise BadParameter(click.style(f'\n{e!s}', fg='red'))
    if not (plugin_dir / plugin_name / 'migrations').is_dir():
        raise BadParameter(click.style(f'\nNo migrations/ folder found in "{plugin_dir}"', fg='red'))
    return plugin_dir


# -- Top-level checks --------------------------------------------------------------------------------------------------

def _check(nb_scripts=0, plugin_dir=None, verbose=False):
    _check_history(plugin_dir, verbose)
    _check_contents(plugin_dir, verbose)
    _check_migrations(nb_scripts, plugin_dir, verbose)


def _check_history(plugin_dir=None, verbose=False):
    click.secho('Checking Alembic revision history consistency:')
    revisions_dir = _get_alembic_revisions_dir(plugin_dir)
    script_dir = ScriptDirectory(ALEMBIC_TESTENV_DIR, version_locations=[revisions_dir])
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
    rev_files = _get_alembic_revision_files(plugin_dir)[::-1]
    if verbose:
        click.secho(_indent(f'{len(rev_files)} revision files found'), fg='cyan')
    for rev_file in rev_files:
        content = rev_file.read_text()
        _check_consistent_revision_hash(content, rev_file.name, rev_file)
        _check_server_default_in_non_nullable_column(content, rev_file)
    click.secho(_indent('Revision hashes are consistent'), fg='green')
    click.secho(_indent('No server defaults missing'), fg='green')


def _check_migrations(nb_scripts=0, plugin_dir=None, verbose=False):
    """Check that the revision scripts upgrade and downgrade cleanly.

    The DB state is only ever changed by alembic, starting from a DB created
    with `indico db prepare`. The diffs from `results` are only checked for
    emptiness and never executed, since it can order drops wrongly (e.g.
    functions before the indexes that use them):

    1. Copy it to DB1, downgrade DB1 to the revision before the oldest one
       checked and copy DB1 to DB2, so both start out identical.
    2. For each revision, oldest first, upgrade DB2, downgrade it again and diff
       it against DB1: an empty diff proves the downgrade reverts the upgrade.
    3. Upgrade both DBs to that revision before checking the next one.
    4. Diff DB1 against the freshly prepared DB: an empty diff proves the
       upgrades lead to the same schema as `indico db prepare`.

    :param nb_scripts: Number of revision scripts to check.
    """
    click.secho('Checking Alembic revision scripts (older to newer):')
    config = _get_alembic_config(plugin_dir)
    script_dir = ScriptDirectory.from_config(config)
    revisions = list(script_dir.walk_revisions())
    revisions = revisions[:nb_scripts] if nb_scripts else revisions
    for revision in revisions:
        if isinstance(revision.down_revision, tuple):
            raise ClickException(f'Revision {revision.revision} is a merge revision, which is not supported')
    total_revisions = len(revisions)
    with _get_db_context(verbose) as (db_eng, dbdiff_eng, dbclean_eng):
        _copy_db(DBCLEAN_NAME, DB_NAME)
        click.secho(_indent(f'Downgrading test DB by {total_revisions} revisions...'), fg='cyan')
        for idx, revision in enumerate(revisions):
            _downgrade(db_eng, config, revision, progress=f'[{total_revisions - idx}/{total_revisions}]')
        _copy_db(DB_NAME, DBDIFF_NAME)
        for idx, revision in enumerate(reversed(revisions)):
            progress = f'[{idx + 1}/{total_revisions}]'
            _upgrade(dbdiff_eng, config, revision, progress=progress)
            _downgrade(dbdiff_eng, config, revision, progress=progress)
            if diff := _get_db_diff(db_eng, dbdiff_eng):
                click.secho(
                    _indent(f'{progress} Revision {revision.revision} is not reverted by its downgrade'), fg='red'
                )
                raise ClickException(
                    f'Upgrading and downgrading revision {revision.revision} leaves these changes:\n\n{diff}'
                )
            _upgrade(db_eng, config, revision, progress=progress)
            _upgrade(dbdiff_eng, config, revision, progress=progress)
            click.secho(_indent(f'{progress} Revision {revision.revision} is correct'), fg='green')
        if diff := _get_db_diff(db_eng, dbclean_eng):
            click.secho(_indent('Upgraded DB differs from a freshly prepared one'), fg='red')
            raise ClickException(f'The upgraded DB needs these changes to match `indico db prepare`:\n\n{diff}')
        click.secho(_indent('All revisions are correct'), fg='green')


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
    rev_files = _get_alembic_revision_files(plugin_dir)
    if len(migrations) < len(rev_files):
        for filename in rev_files[len(migrations):]:
            click.secho(_indent(f'Revision file {filename.name} is orphaned'), fg='red')
        raise ClickException(click.style('Orphaned revisions found', fg='red'))
    click.secho(_indent('No orphaned revision was found'), fg='green')


def _check_revision_file_order(migrations, plugin_dir=None):
    """Check that the Alembic revision and their filenames have the same ordering.

    This uses the Alembic migration history as the canonical order and expects the
    Alembic revision files to be named so that the ascending order matches.  If
    any Alembic revision file is out of order, the expected solution is to modify
    the datetime segment of the filename.
    """
    rev_files = _get_alembic_revision_files(plugin_dir)
    for migration, rev_file in zip(migrations, rev_files, strict=True):
        filename_rev = REGEX_REV_FILENAME.findall(rev_file.name)[0]
        if migration.revision != filename_rev:
            click.secho(_indent(f'File for revision {filename_rev} is out of order'), fg='yellow')
            click.secho(_indent(f'Expected {migration.revision} instead'), fg='yellow')
            raise ClickException(click.style('Revision files are out of order', fg='red'))
    click.secho(_indent('All revision history files are sorted'), fg='green')


# -- Check contents operations -----------------------------------------------------------------------------------------

def _check_consistent_revision_hash(content, file_name, file_path):
    """Check that the alembic revision hash in the code matches the one in the docstring."""
    file_name_hash = REGEX_REV_FILENAME.findall(file_name)[0]
    code_hash = REGEX_REV_CODE_HASH.findall(content)[0]
    docstring_hash = REGEX_REV_DOCSTRING_HASH.findall(content)[0]
    if file_name_hash != code_hash or docstring_hash != code_hash:
        click.secho(_indent(f'Revision hash does not match the hash in the docstring in {file_path}.'), fg='red')
        raise ClickException(click.style('Mismatch in revision hash found', fg='red'))


def _check_server_default_in_non_nullable_column(content, file_path):
    """Check that adding non-nullable columns to an existing table includes a server default."""
    for match in REGEX_ADD_COLUMN.finditer(content):
        body = match.group('body')
        if REGEX_NON_NULLABLE.search(body) and not REGEX_SERVER_DEFAULT.search(body):
            click.secho(_indent(f'Non-nullable column has no server_default set in {file_path}.'), fg='red')
            raise ClickException(click.style('Missing server default in non-nullable column', fg='red'))


# -- Check script operations -------------------------------------------------------------------------------------------

@contextmanager
def _alembic_connection(db_eng, config, failure_msg):
    try:
        with db_eng.begin() as conn:
            config.attributes['connection'] = conn
            yield
    except Exception:
        click.secho(_indent(failure_msg), fg='red')
        raise


def _upgrade(db_eng, config, revision, *, progress):
    """Upgrade a DB to the given revision."""
    with _alembic_connection(db_eng, config, f'{progress} Revision {revision.revision} cannot be applied (upgrade)'):
        alembic.command.upgrade(config, revision.revision)


def _downgrade(db_eng, config, revision, *, progress):
    """Downgrade a DB to the revision before the given one."""
    with _alembic_connection(db_eng, config, f'{progress} Revision {revision.revision} cannot be applied (downgrade)'):
        # The first revision has no parent so downgrading it goes to alembic's 'base'
        alembic.command.downgrade(config, revision.down_revision or 'base')


# -- DB context functions ----------------------------------------------------------------------------------------------

@contextmanager
def _get_db_context(verbose=False):
    try:
        click.secho(_indent('Setting up test DBs...'), fg='cyan')
        _prepare_clean_db(verbose)
        # Postgres can't copy or drop a DB that has open connections so none are pooled
        yield tuple(create_engine(_build_db_uri(name), poolclass=NullPool)
                    for name in (DB_NAME, DBDIFF_NAME, DBCLEAN_NAME))
    except Exception as e:
        if verbose:
            click.secho(traceback.format_exc().rstrip(), fg='red')
        raise ClickException(click.style(str(e), fg='red')) from e
    finally:
        click.secho(_indent('Tearing down test DBs...'), fg='cyan')
        _destroy_dbs()


def _build_db_uri(dbname):
    # Host and port come from libpq's PGHOST and PGPORT
    return f'postgresql://{PG_USER}@/{dbname}'


# -- DB helper functions -----------------------------------------------------------------------------------------------

def _prepare_clean_db(verbose=False):
    try:
        if 'PGUSER' not in os.environ:
            _run(['createuser', PG_USER])
        _run(['createdb', '-O', PG_USER, DBCLEAN_NAME])
        _run(['psql', DBCLEAN_NAME, '-c', 'CREATE EXTENSION unaccent;'])
        _run(['psql', DBCLEAN_NAME, '-c', 'CREATE EXTENSION pg_trgm;'])
        _run(['indico', 'db', 'prepare'])
    except Exception as e:
        if verbose:
            click.secho(_indent(f'Failed to set up the clean test DB due to: {e}'), fg='red')
        raise RuntimeError('Clean test DB could not be initialized') from e


def _destroy_dbs():
    _drop_db(DB_NAME)
    _drop_db(DBDIFF_NAME)
    _drop_db(DBCLEAN_NAME)
    if 'PGUSER' not in os.environ:
        _drop_db_user(PG_USER)


def _drop_db(db_name):
    # Check if database exists. Source: https://stackoverflow.com/a/17757560/1901977
    if _run(['psql', 'postgres', '-XtAc', f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"]) == '1':  # noqa: S608
        _run(['dropdb', db_name])


def _copy_db(source_db, target_db):
    _run(['createdb', '-O', PG_USER, '-T', source_db, target_db])


def _drop_db_user(db_user):
    # Check if user exists. Source: https://stackoverflow.com/a/8546783/1901977
    if _run(['psql', 'postgres', '-XtAc', f"SELECT 1 FROM pg_roles WHERE rolname='{db_user}'"]) == '1':  # noqa: S608
        _run(['dropuser', db_user])


def _get_db_diff(base_eng, target_eng):
    with base_eng.connect() as base_conn, target_eng.connect() as target_conn:
        migration = Migration(base_conn, target_conn)
        migration.set_safety(False)
        migration.add_all_changes()
        return migration.sql


# -- Alembic helper functions ------------------------------------------------------------------------------------------

def _get_alembic_config(plugin_dir=None, stdout=sys.stdout):
    """Configure alembic for running against revisions."""
    config = alembic.config.Config(ALEMBIC_INI_FILE, stdout=stdout)
    config.set_main_option('script_location', str(ALEMBIC_TESTENV_DIR))
    config.set_main_option('version_locations', str(_get_alembic_revisions_dir(plugin_dir)))
    return config


def _get_alembic_revisions_dir(plugin_dir=None):
    if plugin_dir:
        return next(plugin_dir.glob('*/migrations'))
    return Path(INDICO_DIR) / 'indico' / 'migrations' / 'versions'


def _get_alembic_revision_files(plugin_dir=None):
    revisions_dir = _get_alembic_revisions_dir(plugin_dir)
    return sorted(entry for entry in revisions_dir.iterdir() if REGEX_REV_FILENAME.match(entry.name))


# -- Environment helper functions --------------------------------------------------------------------------------------

def _set_test_environment(plugin_name=None, verbose=False):
    if verbose:
        click.secho('Setting up test environment variables...', fg='cyan')
    # Minimal indico.conf settings
    indico_conf = {
        'SECRET_KEY': '*' * 16,
        'BASE_URL': 'http://localhost/',
        'CELERY_BROKER': 'redis://127.0.0.1:6379/0',
        'REDIS_CACHE_URL': 'redis://127.0.0.1:6379/1',
        'DEBUG': True,
        'PLUGINS': [plugin_name] if plugin_name else [],
        'SQLALCHEMY_DATABASE_URI': _build_db_uri(DBCLEAN_NAME)
    }
    os.environ['INDICO_CONFIG'] = '/dev/null'
    os.environ['INDICO_CONF_OVERRIDE'] = repr(indico_conf)
    os.environ['INDICO_ALWAYS_DOWNGRADE'] = 'yes'
    if plugin_name:
        os.environ['ALEMBIC_VERSION_TEST_DB'] = f'alembic_version_plugin_{plugin_name}'


# -- Misc helper functions ---------------------------------------------------------------------------------------------

def _get_plugin_name(plugin_dir):
    # TODO: Is this the best way to get the plugin name?
    packages = [x.parent.name for x in plugin_dir.glob('*/__init__.py')]
    if not packages:
        raise ClickException(f'No plugin package found in {plugin_dir}')
    if len(packages) > 1:
        raise ClickException(f'More than one plugin package in {plugin_dir}')
    return packages[0]


def _indent(msg, level=4):
    indentation = level * ' '
    return indentation + msg.replace('\n', '\n' + indentation)


def _run(cmd, input_=''):
    with subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE) as pipes:
        stdout, stderr = pipes.communicate(input=input_)
        if pipes.returncode != 0:
            error = stderr.decode('unicode_escape').strip()
            raise ClickException(error)
        return stdout.decode('unicode_escape').strip()


# -- Entrypoint --------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
