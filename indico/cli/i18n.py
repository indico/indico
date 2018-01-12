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
import re
import sys
from distutils.dist import Distribution
from functools import wraps
from pkgutil import walk_packages

import click
from babel.messages import frontend
from babel.messages.pofile import read_po
from flask import current_app
from flask.helpers import get_root_path

from indico.cli.core import cli_group
from indico.util.console import cformat


@cli_group()
def cli():
    os.chdir(os.path.join(get_root_path('indico'), '..'))


TRANSLATIONS_DIR = 'indico/translations'
MESSAGES_POT = os.path.join(TRANSLATIONS_DIR, 'messages.pot')
MESSAGES_JS_POT = os.path.join(TRANSLATIONS_DIR, 'messages-js.pot')

DEFAULT_OPTIONS = {
    'init_catalog': {
        'output_file': MESSAGES_POT,
        'output_dir': TRANSLATIONS_DIR
    },
    'extract_messages': {
        'keywords': 'N_:1,2',
        'width': '120',
        'output_file': MESSAGES_POT,
        'mapping_file': 'babel.cfg'
    },
    'compile_catalog': {
        'domain': 'messages',
        'directory': TRANSLATIONS_DIR
    },
    'update_catalog': {
        'input_file': MESSAGES_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages'
    },

    # JavaScript
    'init_catalog_js': {
        'output_file': MESSAGES_JS_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-js'
    },
    'extract_messages_js': {
        'keywords': ['$T', 'gettext', 'ngettext:1,2'],
        'width': '120',
        'output_file': MESSAGES_JS_POT,
        'mapping_file': 'babel-js.cfg',
        'no_default_keywords': '1'
    },
    'update_catalog_js': {
        'input_file': MESSAGES_JS_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-js'
    }
}


def find_packages(path, prefix=""):
    yield prefix
    prefix = prefix + "."
    for _, name, ispkg in walk_packages(path, prefix):
        if ispkg:
            yield name


def wrap_distutils_command(command_class):
    @wraps(command_class)
    def _wrapper(**kwargs):

        import indico

        command = command_class(Distribution({
            'name': 'indico',
            'version': indico.__version__,
            'packages': find_packages(indico.__path__, indico.__name__)
        }))

        for key, val in kwargs.items():
            setattr(command, key, val)

        command.finalize_options()
        command.run()

    return _wrapper


cmd_list = ['init_catalog', 'extract_messages', 'update_catalog']
cmd_list += [cmd + '_js' for cmd in cmd_list]
cmd_list.append('compile_catalog')


for cmd_name in cmd_list:
    cmd_class = getattr(frontend, re.sub(r'_js$', '', cmd_name))

    cmd = click.command(cmd_name)(wrap_distutils_command(cmd_class))
    for opt, short_opt, description in cmd_class.user_options:
        long_opt_name = opt.rstrip('=')
        var_name = long_opt_name.replace('-', '_')
        opts = ['--' + long_opt_name]

        if short_opt:
            opts.append('-' + short_opt)

        default = DEFAULT_OPTIONS.get(cmd_name, {}).get(var_name)
        is_flag = not opt.endswith('=')
        cmd = click.option(*(opts + [var_name]), is_flag=is_flag, default=default, help=description)(cmd)

    cli.add_command(cmd)


@cli.command()
def check_format_strings():
    """Check whether format strings match.

    This helps finding cases where e.g. the original string uses
    ``{error}`` but the translation uses ``{erro}``, resulting
    in errors when using the translated string.
    """
    root_path = os.path.join(current_app.root_path, 'translations')
    paths = set()
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.endswith('.po'):
                paths.add(os.path.join(root, file))
    all_valid = True
    for path in paths:
        invalid = _get_invalid_po_format_strings(path)
        if invalid:
            all_valid = False
            click.echo('Found invalid format strings in {}'.format(os.path.relpath(path, root_path)))
            for item in invalid:
                click.echo(cformat('%{yellow}{}%{reset} | %{yellow!}{}%{reset}\n%{red}{}%{reset} != %{red!}{}%{reset}')
                           .format(item['orig'], item['trans'],
                                   list(item['orig_placeholders']), list(item['trans_placeholders'])))
            click.echo()
    sys.exit(0 if all_valid else 1)


def _get_invalid_po_format_strings(path):
    with open(path, 'rb') as f:
        po_data = read_po(f)
    invalid = []
    for msg in po_data:
        all_orig = msg.id if isinstance(msg.id, tuple) else (msg.id,)
        all_trans = msg.string if isinstance(msg.string, tuple) else (msg.string,)
        if not any(all_trans):  # not translated
            continue
        for orig, trans in zip(all_orig, all_trans):
            # brace format only; python-format (%s etc) is too vague
            # since there are many strings containing e.g. just `%`
            # which are never used for formatting, and babel's
            # `_validate_format` checker fails on those too
            orig_placeholders = set(re.findall(r'(\{[^}]+\})', orig))
            trans_placeholders = set(re.findall(r'(\{[^}]+\})', trans))
            if orig_placeholders != trans_placeholders:
                invalid.append({
                    'orig': orig,
                    'trans': trans,
                    'orig_placeholders': orig_placeholders,
                    'trans_placeholders': trans_placeholders
                })
    return invalid
