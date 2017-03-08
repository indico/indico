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

from __future__ import unicode_literals

import os
import re
from functools import wraps

import click
from babel.messages import frontend
from distutils.dist import Distribution
from flask.helpers import get_root_path
from pkgutil import walk_packages

from indico.cli.core import cli_group


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
        'keywords': '$T',
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
