# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import errno
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from functools import wraps
from itertools import chain
from pathlib import Path
from pkgutil import walk_packages

import click
from babel.messages import frontend
from babel.messages.pofile import read_po
from flask.helpers import get_root_path
from setuptools import find_packages
from setuptools.dist import Distribution

from indico.util.console import cformat


@click.group()
def cli():
    os.chdir(os.path.join(get_root_path('indico'), '..'))


INDICO_DIR = os.path.join(get_root_path('indico'), '..')
TRANSLATIONS_DIR = 'indico/translations'
MESSAGES_POT = os.path.join(TRANSLATIONS_DIR, 'messages.pot')
MESSAGES_JS_POT = os.path.join(TRANSLATIONS_DIR, 'messages-js.pot')
MESSAGES_REACT_POT = os.path.join(TRANSLATIONS_DIR, 'messages-react.pot')

DEFAULT_OPTIONS = {
    'init_catalog': {
        'input_file': MESSAGES_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages'
    },
    'extract_messages': {
        'keywords': 'L_',
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
        'input_file': MESSAGES_JS_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-js'
    },
    'extract_messages_js': {
        'keywords': '$T gettext ngettext:1,2 pgettext:1c,2 npgettext:1c,2,3',
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
        'input_file': MESSAGES_REACT_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-react'
    },
    'update_catalog_react': {
        'input_file': MESSAGES_REACT_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-react'
    },
}


def _get_plugin_options(cmd_name, plugin_dir):
    return {
        'init_catalog': {
            'input_file': _get_messages_pot(plugin_dir),
            'output_dir': _get_translations_dir(plugin_dir),
        },
        'extract_messages': {
            'output_file': _get_messages_pot(plugin_dir),
            'mapping_file': 'babel.cfg' if os.path.isfile(os.path.join(plugin_dir, 'babel.cfg')) else '../babel.cfg'
        },
        'compile_catalog': {
            'directory': _get_translations_dir(plugin_dir),
            'use_fuzzy': True,
        },
        'update_catalog': {
            'input_file': _get_messages_pot(plugin_dir),
            'output_dir': _get_translations_dir(plugin_dir),
        },

        # JavaScript
        'init_catalog_js': {
            'input_file': _get_messages_js_pot(plugin_dir),
            'output_dir': _get_translations_dir(plugin_dir),
        },
        'extract_messages_js': {
            'keywords': '$t gettext ngettext:1,2 pgettext:1c,2 npgettext:1c,2,3',
            'output_file': _get_messages_js_pot(plugin_dir),
            'mapping_file': 'babel-js.cfg' if os.path.isfile(os.path.join(plugin_dir, 'babel-js.cfg'))
                            else '../babel-js.cfg'
        },
        'update_catalog_js': {
            'input_file': _get_messages_js_pot(plugin_dir),
            'output_dir': _get_translations_dir(plugin_dir),
        },

        # JavaScript / React
        'init_catalog_react': {
            'input_file': _get_messages_react_pot(plugin_dir),
            'output_dir': _get_translations_dir(plugin_dir),
        },
        'update_catalog_react': {
            'input_file': _get_messages_react_pot(plugin_dir),
            'output_dir': _get_translations_dir(plugin_dir),
        },
    }[cmd_name]


@contextmanager
def _chdir(path):
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


def _validate_plugin_dir(check_tx=False):
    def _validate_dir(ctx, param, plugin_dir):
        if check_tx:
            if not os.path.exists(os.path.join(plugin_dir, '.tx', 'config')):
                raise click.BadParameter(f'no transifex configuration found in {plugin_dir}.')
        if not os.path.exists(os.path.join(plugin_dir, 'setup.py')):
            raise click.BadParameter(f'no setup.py found in {plugin_dir}.')
        if not list(Path(plugin_dir).glob('*/translations')):
            raise click.BadParameter(f'no translations folder found in {plugin_dir}.')
        return plugin_dir

    return _validate_dir


def _validate_all_plugins_dir(ctx, param, value):
    plugin_dirs = []
    for plugin_dir in os.listdir(value):
        try:
            _validate_plugin_dir()(None, None, os.path.join(value, plugin_dir))
        except click.BadParameter:
            continue
        plugin_dirs.append(os.path.join(value, plugin_dir))
    if not plugin_dirs:
        raise click.BadParameter(f'{value} does not contain valid plugins or a plugin with a translation directory.')
    return plugin_dirs


def _get_translations_dir(path):
    if translation_dir := list(Path(path).glob('*/translations')):
        return translation_dir[0]
    return None


def _get_messages(path, resource_name):
    if resource_name not in ('messages.pot', 'messages-js.pot', 'messages-react.pot'):
        return None
    if translations_dir := _get_translations_dir(path):
        return os.path.join(translations_dir, resource_name)
    return None


def _get_messages_pot(path):
    return _get_messages(path, 'messages.pot')


def _get_messages_js_pot(path):
    return _get_messages(path, 'messages-js.pot')


def _get_messages_react_pot(path):
    return _get_messages(path, 'messages-react.pot')


def find_indico_packages(path, prefix=''):
    yield prefix
    prefix = prefix + '.'
    for _, name, ispkg in walk_packages(path, prefix):
        if ispkg:
            yield name


def _get_indico_distribution():
    import indico

    return Distribution({
        'name': 'indico',
        'version': indico.__version__,
        'packages': list(find_indico_packages(indico.__path__, indico.__name__))
    })


def _get_plugin_distribution(plugin_dir):
    packages = [x for x in find_packages(plugin_dir) if '.' not in x]
    assert len(packages) == 1
    return Distribution({
        'name': packages[0],
        'packages': packages
    })


def wrap_distutils_command(command_class, plugin_dir=None):
    @wraps(command_class)
    def _wrapper(**kwargs):

        dist = _get_plugin_distribution(plugin_dir) if plugin_dir else _get_indico_distribution()
        command = command_class(dist)

        for key, val in kwargs.items():
            setattr(command, key, val)

        command.finalize_options()
        command.run()

    return _wrapper


def _run_command(cmd_name, extra=None):
    cmd_class = getattr(frontend, re.sub(r'_(js|react)$', '', cmd_name))
    options = DEFAULT_OPTIONS.get(cmd_name, {})
    if extra:
        options.update(extra)
    if plugin_dir := options.get('plugin_dir'):
        options.update(_get_plugin_options(cmd_name, plugin_dir))
    cmd = wrap_distutils_command(cmd_class, plugin_dir=plugin_dir)
    cmd(**options)


def _common_translation_options(require_js=True, require_locale=False, plugin=False, all_plugins=False):
    def decorator(fn):
        fn = click.option('--python', is_flag=True, help='i18n used in python and Jinja code.')(fn)
        fn = click.option('--react', is_flag=True, help='i18n used in react code.')(fn)
        if require_js:
            fn = click.option('--javascript', is_flag=True, help='i18n used in javascript code.')(fn)
        else:  # the only command that does not require js is compile_catalog which checks the string format
            fn = click.option('--no-check', is_flag=True, required=False,
                              help='Skip running the string format validation.')(fn)
        if require_locale:
            fn = click.option('--locale', required=True)(fn)
        elif require_locale is not None:
            fn = click.option('--locale', required=False)(fn)
        if plugin:
            fn = click.argument('plugin_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True),
                                callback=_validate_plugin_dir())(fn)
        elif all_plugins:
            fn = click.argument('plugins_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True),
                                callback=_validate_all_plugins_dir)(fn)
        return fn
    return decorator


def compile_catalog_react(directory=INDICO_DIR, locale=''):
    """Compile react catalogs."""
    translations_dir = _get_translations_dir(directory)
    locales = [locale] if locale else os.listdir(translations_dir)
    try:
        for loc in locales:
            po_file = os.path.join(translations_dir, loc, 'LC_MESSAGES', 'messages-react.po')
            json_file = os.path.join(translations_dir, loc, 'LC_MESSAGES', 'messages-react.json')
            if not os.path.exists(po_file):
                continue
            with _chdir(INDICO_DIR):
                output = subprocess.check_output(['npx', 'react-jsx-i18n', 'compile', po_file], encoding='utf-8')
            json.loads(output)  # just to be sure the JSON is valid
            with open(json_file, 'w') as f:
                f.write(output)
    except subprocess.CalledProcessError as err:
        click.secho('Error: ' + err, fg='red', bold=True, err=True)


def extract_messages_react(directory=INDICO_DIR):
    """Extract messages for react."""
    if directory is INDICO_DIR:
        paths = [os.path.join('indico', 'web', 'client'), os.path.join('indico', 'modules')]
    else:
        packages = [x for x in find_packages(directory) if '.' not in x]
        assert len(packages) == 1
        client_path = os.path.join(directory, packages[0], 'client')
        module_path = os.path.join(directory, packages[0], 'modules')
        paths = []
        if os.path.exists(client_path):
            paths.append(client_path)
        if os.path.exists(module_path):
            paths.append(module_path)
        if not paths:
            return
    with _chdir(INDICO_DIR):
        output = subprocess.check_output(['npx', 'react-jsx-i18n', 'extract'] + paths,
                                         env=dict(os.environ, FORCE_COLOR='1'))
    with open(_get_messages_react_pot(directory), 'wb') as f:
        f.write(output)


def po_file_empty(path):
    try:
        with open(path, 'rb') as f:
            po_data = read_po(f)
    except OSError as e:
        if e.errno == errno.ENOENT:
            return False
        raise
    return not po_data


def remove_empty_pot_files(path, python=False, javascript=False, react=False):
    """Remove empty .pot files with no msgid strings after extraction."""
    if python and po_file_empty(_get_messages_pot(path)):
        os.remove(_get_messages_pot(path))
    if javascript and po_file_empty(_get_messages_js_pot(path)):
        os.remove(_get_messages_js_pot(path))
    if react and po_file_empty(_get_messages_react_pot(path)):
        os.remove(_get_messages_react_pot(path))


@cli.group('compile', short_help='Catalog compilation command for indico and indico plugins.')
def compile_catalog():
    """Catalog compilation command for indico and indico plugins."""


@cli.group('extract', short_help='Message extraction command for indico and indico plugins.')
def extract_messages():
    """Message extraction command for indico and indico plugins."""


@cli.group('init', short_help='New catalog initialization command for indico and indico plugins.')
def init_catalog():
    """Catalog initialization command for indico and indico plugin.

    The sub commands take the new locale to be initialized as argument.
    """


@cli.group('update', short_help='Catalog merging command for indico and indico plugins.')
def update_catalog():
    """Catalog merging command for indico and indico plugins."""


def _indico_command(babel_cmd, python, javascript, react, locale, no_check):
    extra = {}
    if locale:
        extra['locale'] = locale
    if not no_check:
        if not _check_format_strings():
            click.secho('Exiting compile command for indico due to invalid format strings.', fg='red', bold=True,
                        err=True)
            sys.exit(1)
    try:
        if python:
            _run_command(babel_cmd, extra=extra)
        if javascript:
            _run_command(f'{babel_cmd}_js', extra=extra)
        if react:
            if babel_cmd == 'compile_catalog':
                compile_catalog_react(locale=extra.get('locale'))
            elif babel_cmd == 'extract_messages':
                extract_messages_react()
            else:
                _run_command(f'{babel_cmd}_react', extra=extra)
    except Exception as err:
        click.secho(f'Error running {babel_cmd} for indico - {err}', fg='red', bold=True, err=True)
    if babel_cmd == 'extract_messages':
        remove_empty_pot_files(INDICO_DIR, python=python, javascript=javascript, react=react)


def _plugin_command(babel_cmd, python, javascript, react, locale, no_check, plugin_dir):
    extra = {}
    if locale:
        extra['locale'] = locale
    extra['plugin_dir'] = plugin_dir

    with _chdir(plugin_dir):
        click.secho(f'plugin: {plugin_dir}', fg='white', bold=True)
        if not no_check:
            translations_dir = _get_translations_dir(plugin_dir)
            if not _check_format_strings(translations_dir):
                click.secho(f'Exiting compile command for {plugin_dir} due to invalid format strings.', fg='red',
                            bold=True, err=True)
                return
        try:
            if python:
                _run_command(babel_cmd, extra=extra)
            if javascript:
                _run_command(f'{babel_cmd}_js', extra=extra)
            if react:
                if babel_cmd == 'compile_catalog':
                    compile_catalog_react(plugin_dir, locale=extra.get('locale'))
                elif babel_cmd == 'extract_messages':
                    extract_messages_react(plugin_dir)
                else:
                    _run_command(f'{babel_cmd}_react', extra=extra)
        except Exception as err:
            click.secho(f'Error running {babel_cmd} for {plugin_dir} - {err}', fg='red', bold=True, err=True)
        if babel_cmd == 'extract_messages':
            remove_empty_pot_files(plugin_dir, python=python, javascript=javascript, react=react)


def _command(**kwargs):
    babel_cmd = kwargs.get('babel_cmd')
    python = kwargs.get('python')
    javascript = kwargs.get('javascript')
    react = kwargs.get('react')
    locale = kwargs.get('locale')
    plugin_dir = kwargs.get('plugin_dir')
    plugins_dir = kwargs.get('plugins_dir')
    no_check = kwargs.get('no_check', True)

    if not (python or react or javascript):
        python = react = javascript = True
        if babel_cmd == 'compile_catalog':
            javascript = False

    if plugin_dir:
        _plugin_command(babel_cmd, python, javascript, react, locale, no_check, plugin_dir)
    elif plugins_dir:
        for plugin_dir in plugins_dir:
            _plugin_command(babel_cmd, python, javascript, react, locale, no_check, plugin_dir)
    else:
        _indico_command(babel_cmd, python, javascript, react, locale, no_check)


def _make_command(group, cmd_name, babel_cmd, **kwargs):
    cmd_group = group.command(cmd_name, short_help=f'Perform {babel_cmd} operation on {cmd_name}')

    @_common_translation_options(**kwargs)
    def wrapper(**kwargs):
        _command(babel_cmd=babel_cmd, **kwargs)

    return cmd_group(wrapper)


_make_command(compile_catalog, 'indico', 'compile_catalog', require_js=False)
_make_command(extract_messages, 'indico', 'extract_messages', require_locale=None)
_make_command(update_catalog, 'indico', 'update_catalog')
_make_command(init_catalog, 'indico', 'init_catalog', require_locale=True)

_make_command(compile_catalog, 'plugin', 'compile_catalog', require_js=False,
              plugin=True)
_make_command(extract_messages, 'plugin', 'extract_messages', plugin=True, require_locale=None)
_make_command(update_catalog, 'plugin', 'update_catalog', plugin=True)
_make_command(init_catalog, 'plugin', 'init_catalog', require_locale=True,
              plugin=True)

_make_command(compile_catalog, 'all-plugins', 'compile_catalog', require_js=False,
              all_plugins=True)
_make_command(extract_messages, 'all-plugins', 'extract_messages', all_plugins=True,
              require_locale=None)
_make_command(update_catalog, 'all-plugins', 'update_catalog', all_plugins=True)
_make_command(init_catalog, 'all-plugins', 'init_catalog', require_locale=True,
              all_plugins=True)


@cli.group('push', short_help='Push .pot files to transifex for indico and indico plugins.')
def push():
    """Push .pot files to transifex for indico and indico plugins."""


def _push():
    """Push .pot files to transifex."""
    try:
        subprocess.run(['tx', 'push', '-s'], check=True)
    except subprocess.CalledProcessError:
        click.secho('Error pushing to transifex', fg='red', bold=True, err=True)


@push.command('indico', short_help='Push .pot files to Transifex for indico.')
def push_indico():
    """Push .pot files to Transifex for indico."""
    _push()


@push.command('plugin', short_help='Push .pot files to Transifex for a plugin.')
@click.argument('plugin_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True),
                callback=_validate_plugin_dir(check_tx=True))
def push_plugin(plugin_dir):
    """Push .pot files to transifex for a plugin."""
    with _chdir(plugin_dir):
        _push()


@push.command('all-plugins', short_help='Push .pot files to Transifex for multiple plugins.')
@click.argument('plugins_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True),
                callback=_validate_all_plugins_dir)
def push_all_plugins(plugins_dir):
    """Push .pot files to transifex for multiple plugins in a directory."""
    parent_directory = Path(plugins_dir[0]).parent.absolute()
    with _chdir(parent_directory):
        _push()


@cli.group('pull', short_help='Pull translated .po files from Transifex indico and indico plugins.')
def pull():
    """Pull translated .po files from Transifex for indico and indico plugins."""


def _pull(languages, translations_dir=TRANSLATIONS_DIR):
    """Pull translated .po files from Transifex.

    Pulls only the language codes specified in `languages` if present.
    If no `languages`, it pulls all the languages currently available in the translations folder.
    To pull a new language available on Transifex, simply pass the new language code in the argument.
    """
    if not languages:
        languages = [d for d in os.listdir(translations_dir) if os.path.isdir(os.path.join(translations_dir, d))]
        if 'en_US' in languages:
            languages.remove('en_US')
    language_renames = {'zh_Hans_CN': 'zh_CN.GB2312'}  # other lang codes requiring rename should be added here
    language_codes = [language_renames.get(language, language) for language in languages]
    try:
        subprocess.run(['tx', 'pull', '-l', ','.join(language_codes), '-f'], check=True)
        click.secho('Translations updated.', fg='green', bold=True)
    except subprocess.CalledProcessError:
        click.secho('Error pulling from transifex', fg='red', bold=True, err=True)
        sys.exit(1)
    else:
        for code in set(languages) & set(language_renames):
            if os.path.exists(os.path.join(translations_dir, code)):
                shutil.rmtree(os.path.join(translations_dir, code))
            shutil.move(os.path.join(translations_dir, language_renames[code]),
                        os.path.join(translations_dir, code))


@pull.command('indico', short_help='Pull translated .po files from Transifex for indico.')
@click.argument('languages', nargs=-1, required=False)
def pull_indico(languages):
    """Pull translated .po files from Transifex for indico.

    Pulls only the language codes specified in `languages` if present.
    If no `languages`, it pulls all the languages currently available in the translations folder.
    To pull a new language available on Transifex, simply pass the new language code in the argument.
    """
    _pull(languages)


@pull.command('plugin', short_help='Pull translated .po files from Transifex for a plugin.')
@click.argument('plugin_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True),
                callback=_validate_plugin_dir(check_tx=True))
@click.argument('languages', nargs=-1, required=False)
def pull_plugin(plugin_dir, languages):
    """Pull translated .po files from Transifex for a plugin."""
    with _chdir(plugin_dir):
        _pull(languages, _get_translations_dir(plugin_dir))


@pull.command('all-plugins', short_help='Pull translated .po files from Transifex for multiple plugins.')
@click.argument('plugins_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True),
                callback=_validate_all_plugins_dir)
@click.argument('languages', nargs=-1, required=False)
def pull_all_plugins(plugins_dir, languages):
    """Pull translated .po files from Transifex for multiple plugins."""
    parent_directory = Path(plugins_dir[0]).parent.absolute()
    with _chdir(parent_directory):
        if 'en_US' in languages:
            languages.remove('en_US')
        language_renames = {'zh_Hans_CN': 'zh_CN.GB2312'}  # other lang codes requiring rename should be added here
        language_codes = [language_renames.get(language, language) for language in languages]
        try:
            if languages:
                subprocess.run(['tx', 'pull', '-l', ','.join(language_codes), '-f'], check=True)
            else:
                subprocess.run(['tx', 'pull', '-f'], check=True)
            click.secho('Translations updated.', fg='green', bold=True)
        except subprocess.CalledProcessError:
            click.secho('Error pulling from transifex', fg='red', bold=True, err=True)
            sys.exit(1)
        else:
            for code in set(languages) & set(language_renames):
                for plugin_dir in plugins_dir:
                    translations_dir = _get_translations_dir(plugin_dir)
                    if os.path.exists(os.path.join(translations_dir, code)):
                        shutil.rmtree(os.path.join(translations_dir, code))
                    shutil.move(os.path.join(translations_dir, language_renames[code]),
                                os.path.join(translations_dir, code))


def _check_format_strings(root_path='indico/translations'):
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
            click.echo(f'Found invalid format strings in {os.path.relpath(path, root_path)}')
            for item in invalid:
                click.echo(cformat('%{yellow}{}%{reset} | %{yellow!}{}%{reset}\n%{red}{}%{reset} != %{red!}{}%{reset}')
                           .format(item['orig'], item['trans'],
                                   list(item['orig_placeholders']), list(item['trans_placeholders'])))
            click.echo()
    return all_valid


@cli.command()
def check_format_strings():
    """Check whether format strings match.

    This helps finding cases where e.g. the original string uses
    ``{error}`` but the translation uses ``{erro}``, resulting
    in errors when using the translated string.
    """
    all_valid = _check_format_strings()
    if all_valid:
        click.secho('No issues found!', fg='green', bold=True)
    sys.exit(0 if all_valid else 1)


def _extract_placeholders(string):
    return set(re.findall(r'(\{[^}]+\})', string))


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
            orig_placeholders = _extract_placeholders(orig)
            # in some cases the english singular doesn't use the placeholder but rather e.g. "One".
            # but depending on the language (usually with nplurals=1) the singular version MUST include
            # the placeholder, so we need to consider those as well
            orig_plural_placeholders = set(chain.from_iterable(map(_extract_placeholders, all_orig[1:])))
            trans_placeholders = _extract_placeholders(trans)
            if (
                trans_placeholders not in (orig_placeholders, orig_plural_placeholders) or
                (not orig_plural_placeholders and trans_placeholders != orig_placeholders) or
                (not orig_placeholders and trans_placeholders and trans_placeholders != orig_plural_placeholders)
            ):
                invalid.append({
                    'orig': orig,
                    'trans': trans,
                    'orig_placeholders': orig_placeholders,
                    'trans_placeholders': trans_placeholders
                })
    return invalid
