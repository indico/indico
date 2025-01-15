# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import shlex
import subprocess
import sys

import click
from click._compat import should_strip_ansi
from migra import Migration
from sqlalchemy import create_engine, text


def _indent(msg, level=4):
    indentation = level * ' '
    return indentation + msg.replace('\n', '\n' + indentation)


def _checked_call(verbose, args, return_output=False, env=None, input=''):
    cmd = ' '.join([os.path.basename(args[0]), shlex.join(args[1:])])
    if verbose:
        click.echo(click.style(f'** {cmd}', fg='blue', bold=True), err=True)
    kwargs = {}
    if env:
        kwargs['env'] = os.environ | env
    try:
        rv = subprocess.check_output(args, stderr=subprocess.STDOUT, input=input, text=True, **kwargs).strip()
    except OSError as exc:
        click.echo(click.style(f'!! {cmd} failed: {exc}', fg='red', bold=True), err=True)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        click.echo(click.style(f'!! {cmd} failed:', fg='red', bold=True), err=True)
        click.echo(click.style(_indent(exc.output.strip()), fg='yellow', bold=True), err=True)
        sys.exit(1)
    else:
        if return_output:
            return rv
        if verbose > 1 and rv:
            click.echo(click.style(rv, fg='green'), err=True)


def _build_conn_string(dbname):
    pghost = os.environ.get('PGHOST')
    pgport = os.environ.get('PGPORT')
    pguser = os.environ.get('PGUSER')
    parts = ['postgresql://']
    if pguser:
        parts += [pguser, ':@']
    if pghost:
        parts += [pghost]
        if pgport:
            parts += [':', pgport]
    parts += ['/', dbname]
    return ''.join(parts)


@click.command()
@click.argument('dbname', required=False, default='indico')
@click.option('-v', '--verbose', help='Verbose - show called commands; use -vv to also show all output', count=True)
@click.option('-r', '--reverse', help='Reverse - return instead the SQL to go from target to base', is_flag=True)
def main(dbname, verbose, reverse):
    """
    Compare the structure of the database against what's created from the
    models during `indico db prepare`.

    By default the current database is assumed to be named `indico`, but it
    can be overridden.  The database uses for comparison will be named
    `indico_dbdiff` and may not exist. It will be created and dropped
    automatically.

    Since your user may or may not be a database superuser, the database is
    created from a template database named `indico_template`.  You can create
    it using the following SQL commands:

    \b
        createdb indico_template
        psql indico_template -c 'CREATE EXTENSION unaccent;'
        psql indico_template -c 'CREATE EXTENSION pg_trgm;'

    Since this script uses the command-line PostgreSQL tools any other
    configuration should be done using the various environment variables like
    PGHOST, PGPORT and PGUSER) and your `.pgpass` file.
    """
    temp_dbname = 'indico_dbdiff'
    base_conn = None
    target_conn = None

    # create database and dump current/new structures
    _checked_call(verbose, ['createdb', '-T', 'indico_template', temp_dbname])
    try:
        env_override = {'INDICO_CONF_OVERRIDE': repr({'SQLALCHEMY_DATABASE_URI': _build_conn_string(temp_dbname)})}
        _checked_call(verbose, ['indico', 'db', 'prepare', '--force'], env=env_override)

        # create SQLAlchemy engines/connections for base and target db
        base_eng = create_engine(_build_conn_string(temp_dbname))
        target_eng = create_engine(_build_conn_string(dbname))
        base_conn = base_eng.connect()
        target_conn = target_eng.connect()

        version = base_conn.execute(text("SELECT current_setting('server_version_num')::int")).scalar()
        if version < 100000:
            click.echo(click.style('!! This utility requires at least Postgres 10', fg='red', bold=True), err=True)
            sys.exit(1)

        if verbose:
            click.echo(click.style('** Calculating differences', fg='cyan'), err=True)
        # use migra to figure out the SQL diff
        m = Migration(base_conn, target_conn) if reverse else Migration(target_conn, base_conn)
        m.set_safety(False)
        m.add_all_changes()
        diff = m.sql
    finally:
        # clean up connections and engines, so that no open connection remains
        # (otherwise the DROPDB operation won't work)
        if base_conn:
            base_conn.close()
            base_eng.dispose()
        if target_conn:
            target_conn.close()
            target_eng.dispose()
        _checked_call(verbose, ['dropdb', temp_dbname])

    if not diff:
        click.echo(click.style('No changes found :)', fg='green', bold=True), err=True)
        return
    elif should_strip_ansi(sys.stdout):
        click.echo(diff)
    else:
        pretty_diff = _checked_call(verbose, ['pygmentize', '-l', 'sql', '-f', 'terminal256',
                                              '-O', 'style=native,bg=dark'], return_output=True, input=diff)
        click.echo(pretty_diff)


if __name__ == '__main__':
    main()
