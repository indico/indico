# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

import os
import pipes
import subprocess
import sys
import tempfile

import click
from click._compat import should_strip_ansi


click.disable_unicode_literals_warning = True


def _indent(msg, level=4):
    indentation = level * ' '
    return indentation + msg.replace('\n', '\n' + indentation)


def _subprocess_check_output(*popenargs, **kwargs):
    # copied from subprocess.check_output; added the ability to pass data ta stdin
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    stdin_data = kwargs.pop('stdin_data', None)
    if stdin_data:
        kwargs['stdin'] = subprocess.PIPE
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate(stdin_data)
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get('args')
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, output=output)
    return output


def _checked_call(verbose, args, return_output=False, env=None, stdin_data=None):
    cmd = ' '.join([os.path.basename(args[0])] + map(pipes.quote, args[1:]))
    if verbose:
        click.echo(click.style('** {}'.format(cmd), fg='blue', bold=True), err=True)
    kwargs = {}
    if env:
        kwargs['env'] = dict(os.environ, **env)
    try:
        rv = _subprocess_check_output(args, stderr=subprocess.STDOUT, stdin_data=stdin_data, **kwargs).strip()
    except OSError as exc:
        click.echo(click.style('!! {} failed: {}'.format(cmd, exc), fg='red', bold=True), err=True)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        click.echo(click.style('!! {} failed:'.format(cmd), fg='red', bold=True), err=True)
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


def _which(program):
    # taken from http://stackoverflow.com/a/377028/298479
    def _is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if _is_exe(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if _is_exe(exe_file):
                return exe_file
    return None


def _get_apgdiff_cmd(apgdiff):
    if not apgdiff:
        path = _which('apgdiff')
        if path:
            return [path]
    elif '.jar' in apgdiff:
        return ['java', '-jar', apgdiff]
    else:
        return [apgdiff]


@click.command()
@click.argument('dbname', required=False, default='indico')
@click.option('-v', '--verbose', help='Verbose - show called commands; use -vv to also show all output', count=True)
@click.option('--apgdiff', help='Path to apgdiff (or its .jar file)', envvar='APGDIFF',
              type=click.Path(exists=True, dir_okay=False, resolve_path=True))
def main(dbname, verbose, apgdiff):
    """
    Compares the structure of the database against what's created from the
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

    apgdiff needs to be installed. If `apgdiff` is in your PATH it will be
    used; otherwise you need to use `--apgdiff` or the `APGDIFF` env var to
    specify the path to `apgdiff` apgdiff or its .jar file.
    """
    temp_dbname = 'indico_dbdiff'
    apgdiff_cmd = _get_apgdiff_cmd(apgdiff)
    if not apgdiff_cmd:
        raise click.exceptions.UsageError('Could not find apgdiff in PATH; specify the path to a script or the .jar '
                                          'file manually.')
    # create database and dump current/new structures
    _checked_call(verbose, ['createdb', '-T', 'indico_template', temp_dbname])
    try:
        env_override = {'INDICO_CONF_OVERRIDE': repr({'SQLALCHEMY_DATABASE_URI': _build_conn_string(temp_dbname)})}
        _checked_call(verbose, ['indico', 'db', 'prepare'], env=env_override)
        dump_current = tempfile.NamedTemporaryFile(suffix='.sql', prefix='dbdiff-current-')
        dump_fresh = tempfile.NamedTemporaryFile(suffix='.sql', prefix='dbdiff-fresh-')
        _checked_call(verbose, ['pg_dump', '-s', '-f', dump_current.name, dbname])
        _checked_call(verbose, ['pg_dump', '-s', '-f', dump_fresh.name, temp_dbname])
    finally:
        _checked_call(verbose, ['dropdb', temp_dbname])
    # compare them
    diff = _checked_call(verbose, apgdiff_cmd + [dump_current.name, dump_fresh.name],
                         return_output=True).strip()
    if not diff:
        click.echo(click.style('No changes found :)', fg='green', bold=True), err=True)
        return
    elif should_strip_ansi(sys.stdout):
        click.echo(diff)
    else:
        pretty_diff = _checked_call(verbose, ['pygmentize', '-l', 'sql', '-f', 'terminal256',
                                              '-O', 'style=native,bg=dark'], return_output=True, stdin_data=diff)
        click.echo(pretty_diff)


if __name__ == '__main__':
    main()
