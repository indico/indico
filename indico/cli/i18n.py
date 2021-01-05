# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import json
import os
import re
import subprocess
import sys
from distutils.dist import Distribution
from functools import wraps
from pkgutil import walk_packages

import click
from babel.messages import frontend
from babel.messages.pofile import read_po
from flask.helpers import get_root_path

from indico.util.console import cformat


@click.group()
def cli():
    os.chdir(os.path.join(get_root_path('indico'), '..'))


TRANSLATIONS_DIR = 'indico/translations'
MESSAGES_POT = os.path.join(TRANSLATIONS_DIR, 'messages.pot')
MESSAGES_JS_POT = os.path.join(TRANSLATIONS_DIR, 'messages-js.pot')
MESSAGES_REACT_POT = os.path.join(TRANSLATIONS_DIR, 'messages-react.pot')

DEFAULT_OPTIONS = {
    'init_catalog': {
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
    },

    # JavaScript / React
    'init_catalog_react': {
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-react'
    },
    'update_catalog_react': {
        'input_file': MESSAGES_REACT_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-react'
    },
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


def _make_command(cmd_name):
    cmd_class = getattr(frontend, re.sub(r'_(js|react)$', '', cmd_name))
    cmd = click.command(cmd_name.replace('_', '-'))(wrap_distutils_command(cmd_class))
    for opt, short_opt, description in cmd_class.user_options:
        long_opt_name = opt.rstrip('=')
        var_name = long_opt_name.replace('-', '_')
        opts = ['--' + long_opt_name]

        if short_opt:
            opts.append('-' + short_opt)

        default = DEFAULT_OPTIONS.get(cmd_name, {}).get(var_name)
        is_flag = not opt.endswith('=')
        cmd = click.option(*(opts + [var_name]), is_flag=is_flag, default=default, help=description)(cmd)
    return cmd


cmd_list = ['init_catalog', 'extract_messages', 'update_catalog', 'compile_catalog',
            'init_catalog_js', 'extract_messages_js', 'update_catalog_js',
            'init_catalog_react', 'update_catalog_react']


for cmd_name in cmd_list:
    cli.add_command(_make_command(cmd_name))


@cli.command()
def extract_messages_react():
    output = subprocess.check_output(['npx', 'react-jsx-i18n', 'extract', 'indico/web/client/', 'indico/modules/'],
                                     env=dict(os.environ, FORCE_COLOR='1'))
    with open(MESSAGES_REACT_POT, 'wb') as f:
        f.write(output)


@cli.command()
def compile_catalog_react():
    for locale in os.listdir(TRANSLATIONS_DIR):
        po_file = os.path.join(TRANSLATIONS_DIR, locale, 'LC_MESSAGES', 'messages-react.po')
        json_file = os.path.join(TRANSLATIONS_DIR, locale, 'LC_MESSAGES', 'messages-react.json')
        if not os.path.exists(po_file):
            continue
        output = subprocess.check_output(['npx', 'react-jsx-i18n', 'compile', po_file])
        json.loads(output)  # just to be sure the JSON is valid
        with open(json_file, 'wb') as f:
            f.write(output)


@cli.command()
def check_format_strings():
    """Check whether format strings match.

    This helps finding cases where e.g. the original string uses
    ``{error}`` but the translation uses ``{erro}``, resulting
    in errors when using the translated string.
    """
    root_path = 'indico/translations'
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
