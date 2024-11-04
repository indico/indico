# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
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
import tomllib
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from pkgutil import walk_packages

import click
from babel.messages import frontend
from babel.messages.pofile import read_po
from flask.helpers import get_root_path

import indico
from indico.util.console import cformat


# Languages where the name on Transifex does not match what we need locally
LANGUAGE_RENAMES = {'zh_Hans_CN': 'zh_CN.GB2312'}

INDICO_DIR = Path(get_root_path('indico')).parent
TRANSLATIONS_DIR = INDICO_DIR / 'indico' / 'translations'
MESSAGES_POT = TRANSLATIONS_DIR / 'messages.pot'
MESSAGES_JS_POT = TRANSLATIONS_DIR / 'messages-js.pot'
MESSAGES_REACT_POT = TRANSLATIONS_DIR / 'messages-react.pot'

TRANSLATOR_COMMENT_TAG = 'i18n:'

DEFAULT_OPTIONS = {
    'InitCatalog': {
        'input_file': MESSAGES_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages'
    },
    'ExtractMessages': {
        'keywords': 'L_',
        'width': 120,
        'output_file': MESSAGES_POT,
        'mapping_file': 'babel.cfg',
        'input_paths': ['indico'],
        'add_location': 'file',
        'add_comments': TRANSLATOR_COMMENT_TAG,  # Extract translator comments starting with 'i18n:'
        'strip_comments': True,  # Strip the comment tag ('i18n:') from the extracted comments
        'project': 'Indico',
        'version': indico.__version__,
    },
    'CompileCatalog': {
        'domain': 'messages',
        'directory': TRANSLATIONS_DIR
    },
    'UpdateCatalog': {
        'input_file': MESSAGES_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages'
    },

    # JavaScript
    'InitCatalog_js': {
        'input_file': MESSAGES_JS_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-js'
    },
    'ExtractMessages_js': {
        'keywords': '$T gettext ngettext:1,2 pgettext:1c,2 npgettext:1c,2,3',
        'width': 120,
        'output_file': MESSAGES_JS_POT,
        'mapping_file': 'babel-js.cfg',
        'no_default_keywords': True,
        'input_paths': ['indico'],
        'add_location': 'file',
        'add_comments': TRANSLATOR_COMMENT_TAG,  # Extract translator comments starting with 'i18n:'
        'strip_comments': True,  # Strip the comment tag ('i18n:') from the extracted comments
        'project': 'Indico',
        'version': indico.__version__,
    },
    'UpdateCatalog_js': {
        'input_file': MESSAGES_JS_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-js'
    },

    # JavaScript / React
    'InitCatalog_react': {
        'input_file': MESSAGES_REACT_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-react'
    },
    'UpdateCatalog_react': {
        'input_file': MESSAGES_REACT_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-react'
    },
}


def _get_pyproject_version(plugin_dir: Path, data: dict):
    # try a static version
    try:
        return data['project']['version']
    except KeyError:
        pass
    # lookup dynamic version
    if 'version' not in data['project'].get('dynamic', ()):
        raise Exception('Version is missing and not dynamic')
    if data['build-system']['build-backend'] != 'hatchling.build':
        raise Exception('Dynamic versions are only supported for hatchling build backend')
    try:
        version_file_path = data['tool']['hatch']['version']['path']
    except KeyError:
        raise Exception('Version file path is not defined')
    version_file_pattern = data['tool']['hatch']['version'].get('pattern', True)
    # local import because `indico i18n` exists outside dev setups, even though it is not
    # meant to be used there, and hatchling is only guaranteed to be available in a dev setup
    from hatchling.version.core import VersionFile
    vf = VersionFile(plugin_dir, version_file_path)
    return vf.read(pattern=version_file_pattern)


def _get_plugin_options(cmd_name, plugin_dir: Path):
    pyproject = tomllib.loads((plugin_dir / 'pyproject.toml').read_text())
    plugin_name = pyproject['project']['name']
    plugin_version = _get_pyproject_version(plugin_dir, pyproject)
    packages = [x.parent.name for x in plugin_dir.glob('*/__init__.py')]
    assert len(packages) == 1
    return {
        'InitCatalog': {
            'input_file': _get_messages_pot(plugin_dir),
            'output_dir': _get_translations_dir(plugin_dir),
        },
        'ExtractMessages': {
            'output_file': _get_messages_pot(plugin_dir),
            'mapping_file': 'babel.cfg' if (plugin_dir / 'babel.cfg').exists() else '../babel.cfg',
            'input_paths': packages,  # relative to the plugin_dir
            'project': plugin_name,
            'version': plugin_version,
        },
        'CompileCatalog': {
            'directory': _get_translations_dir(plugin_dir),
            'use_fuzzy': True,
        },
        'UpdateCatalog': {
            'input_file': _get_messages_pot(plugin_dir),
            'output_dir': _get_translations_dir(plugin_dir),
        },

        # JavaScript
        'InitCatalog_js': {
            'input_file': _get_messages_js_pot(plugin_dir),
            'output_dir': _get_translations_dir(plugin_dir),
        },
        'ExtractMessages_js': {
            'keywords': '$t gettext ngettext:1,2 pgettext:1c,2 npgettext:1c,2,3',
            'output_file': _get_messages_js_pot(plugin_dir),
            'mapping_file': 'babel-js.cfg' if (plugin_dir / 'babel-js.cfg').exists() else '../babel-js.cfg',
            'input_paths': packages,  # relative to the plugin_dir
            'project': plugin_name,
            'version': plugin_version,
        },
        'UpdateCatalog_js': {
            'input_file': _get_messages_js_pot(plugin_dir),
            'output_dir': _get_translations_dir(plugin_dir),
        },

        # JavaScript / React
        'InitCatalog_react': {
            'input_file': _get_messages_react_pot(plugin_dir),
            'output_dir': _get_translations_dir(plugin_dir),
        },
        'UpdateCatalog_react': {
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
    def _validate_dir(ctx, param, plugin_dir: Path):
        if check_tx:
            if not (plugin_dir / '.tx' / 'config').exists():
                raise click.BadParameter(f'no transifex configuration found in {plugin_dir}.')
        if not (plugin_dir / 'pyproject.toml').exists():
            raise click.BadParameter(f'no pyproject.toml found in {plugin_dir}.')
        if not list(plugin_dir.glob('*/translations')):
            raise click.BadParameter(f'no translations folder found in {plugin_dir}.')
        return plugin_dir

    return _validate_dir


def _validate_all_plugins_dir(ctx, param, value: Path) -> list[Path]:
    plugin_dirs = []
    for plugin_dir in value.iterdir():
        try:
            _validate_plugin_dir()(None, None, plugin_dir)
        except click.BadParameter:
            continue
        plugin_dirs.append(plugin_dir)
    if not plugin_dirs:
        raise click.BadParameter(f'{value} does not contain valid plugins or a plugin with a translation directory.')
    return plugin_dirs


def _get_translations_dir(path: Path) -> Path:
    if translation_dir := list(path.glob('*/translations')):
        return translation_dir[0]
    return None


def _get_messages(path: Path, resource_name) -> Path | None:
    if resource_name not in ('messages.pot', 'messages-js.pot', 'messages-react.pot'):
        return None
    if translations_dir := _get_translations_dir(path):
        return translations_dir / resource_name
    return None


def _get_messages_pot(path) -> Path | None:
    return _get_messages(path, 'messages.pot')


def _get_messages_js_pot(path) -> Path | None:
    return _get_messages(path, 'messages-js.pot')


def _get_messages_react_pot(path) -> Path | None:
    return _get_messages(path, 'messages-react.pot')


def find_indico_packages(path, prefix=''):
    yield prefix
    prefix += '.'
    for __, name, ispkg in walk_packages(path, prefix):
        if ispkg:
            yield name


def wrap_babel_command(command_class):
    @wraps(command_class)
    def _wrapper(**kwargs):
        command = command_class()
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
    cmd = wrap_babel_command(cmd_class)
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
            fn = click.argument('plugin_dir',
                                type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path),
                                callback=_validate_plugin_dir())(fn)
        elif all_plugins:
            fn = click.argument('plugins_dir',
                                type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path),
                                callback=_validate_all_plugins_dir)(fn)
        return fn
    return decorator


def compile_catalog_react(directory: Path = INDICO_DIR, locale=''):
    """Compile react catalogs."""
    translations_dir = _get_translations_dir(directory)
    locales = [locale] if locale else [x.name for x in translations_dir.iterdir() if x.is_dir()]
    try:
        for loc in locales:
            po_file = translations_dir / loc / 'LC_MESSAGES' / 'messages-react.po'
            json_file = translations_dir / loc / 'LC_MESSAGES' / 'messages-react.json'
            if not po_file.exists():
                continue
            with _chdir(INDICO_DIR):
                output = subprocess.check_output(['npx', 'react-jsx-i18n', 'compile', po_file], encoding='utf-8')
            json.loads(output)  # just to be sure the JSON is valid
            json_file.write_text(output)
    except subprocess.CalledProcessError as err:
        click.secho('Error: ' + err, fg='red', bold=True, err=True)


def extract_messages_react(directory: Path = INDICO_DIR):
    """Extract messages for react."""
    if directory == INDICO_DIR:
        paths = [Path('indico/web/client'), Path('indico/modules')]
    else:
        packages = [x.parent.name for x in directory.glob('*/__init__.py')]
        assert len(packages) == 1
        client_path = directory / packages[0] / 'client'
        if not client_path.exists():
            return
        paths = [client_path]
    with _chdir(INDICO_DIR):
        output = subprocess.check_output([
            'npx', 'react-jsx-i18n', 'extract',
            '--ext', 'js,jsx,ts,tsx',
            '--base', directory,
            '--add-location', 'file',
            *paths
        ], env=dict(os.environ, FORCE_COLOR='1', MOCK_FLASK_URLS='1'))
    _get_messages_react_pot(directory).write_bytes(output)


def po_file_empty(path: Path):
    try:
        with path.open('rb') as f:
            po_data = read_po(f)
    except OSError as e:
        if e.errno == errno.ENOENT:
            return False
        raise
    return not po_data


def remove_empty_pot_files(path: Path, python=False, javascript=False, react=False):
    """Remove empty .pot files with no msgid strings after extraction."""
    if python and po_file_empty(_get_messages_pot(path)):
        _get_messages_pot(path).unlink()
    if javascript and po_file_empty(_get_messages_js_pot(path)):
        _get_messages_js_pot(path).unlink()
    if react and po_file_empty(_get_messages_react_pot(path)):
        _get_messages_react_pot(path).unlink()


@click.group()
def cli():
    os.chdir(INDICO_DIR)


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
        if not _check_mismatched_html_tags():
            click.secho('Exiting compile command for indico due to mismatched HTML tags.', fg='red', bold=True,
                        err=True)
            sys.exit(1)
    try:
        if python:
            _run_command(babel_cmd, extra=extra)
        if javascript:
            _run_command(f'{babel_cmd}_js', extra=extra)
        if react:
            if babel_cmd == 'CompileCatalog':
                compile_catalog_react(locale=extra.get('locale'))
            elif babel_cmd == 'ExtractMessages':
                extract_messages_react()
            else:
                _run_command(f'{babel_cmd}_react', extra=extra)
    except Exception as err:
        click.secho(f'Error running {babel_cmd} for indico - {err}', fg='red', bold=True, err=True)
    if babel_cmd == 'ExtractMessages':
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
            if not _check_mismatched_html_tags(translations_dir):
                click.secho(f'Exiting compile command for {plugin_dir} due to invalid format strings.', fg='red',
                            bold=True, err=True)
                return
        try:
            if python:
                _run_command(babel_cmd, extra=extra)
            if javascript:
                _run_command(f'{babel_cmd}_js', extra=extra)
            if react:
                if babel_cmd == 'CompileCatalog':
                    compile_catalog_react(plugin_dir, locale=extra.get('locale'))
                elif babel_cmd == 'ExtractMessages':
                    extract_messages_react(plugin_dir)
                else:
                    _run_command(f'{babel_cmd}_react', extra=extra)
        except Exception as err:
            click.secho(f'Error running {babel_cmd} for {plugin_dir} - {err}', fg='red', bold=True, err=True)
        if babel_cmd == 'ExtractMessages':
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
        if babel_cmd == 'CompileCatalog':
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


_make_command(compile_catalog, 'indico', 'CompileCatalog', require_js=False)
_make_command(extract_messages, 'indico', 'ExtractMessages', require_locale=None)
_make_command(update_catalog, 'indico', 'UpdateCatalog')
_make_command(init_catalog, 'indico', 'InitCatalog', require_locale=True)

_make_command(compile_catalog, 'plugin', 'CompileCatalog', require_js=False, plugin=True)
_make_command(extract_messages, 'plugin', 'ExtractMessages', plugin=True, require_locale=None)
_make_command(update_catalog, 'plugin', 'UpdateCatalog', plugin=True)
_make_command(init_catalog, 'plugin', 'InitCatalog', require_locale=True, plugin=True)

_make_command(compile_catalog, 'all-plugins', 'CompileCatalog', require_js=False, all_plugins=True)
_make_command(extract_messages, 'all-plugins', 'ExtractMessages', all_plugins=True, require_locale=None)
_make_command(update_catalog, 'all-plugins', 'UpdateCatalog', all_plugins=True)
_make_command(init_catalog, 'all-plugins', 'InitCatalog', require_locale=True, all_plugins=True)


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
        languages = [d.name for d in translations_dir.iterdir() if d.is_dir()]
        if 'en_US' in languages:
            languages.remove('en_US')
    language_codes = [LANGUAGE_RENAMES.get(language, language) for language in languages]
    try:
        subprocess.run(['tx', 'pull', '-l', ','.join(language_codes), '-f'], check=True)
        click.secho('Translations updated.', fg='green', bold=True)
    except subprocess.CalledProcessError:
        click.secho('Error pulling from transifex', fg='red', bold=True, err=True)
        sys.exit(1)
    # apply renames for languages where the transifex name and babel locale names do not match
    for code in set(languages) & set(LANGUAGE_RENAMES):
        target_dir = translations_dir / code
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.move(translations_dir / LANGUAGE_RENAMES[code], target_dir)


@pull.command('indico', short_help='Pull translated .po files from Transifex for indico.')
@click.argument('languages', nargs=-1, required=False)
def pull_indico(languages):
    """Pull translated .po files from Transifex for indico.

    Pulls only the language codes specified in `languages` if present.
    If no `languages`, it pulls all the languages currently available in the translations folder.
    To pull a new language available on Transifex, simply pass the new language code in the argument.
    """
    _pull(languages)


def _check_format_strings(root_path: Path = TRANSLATIONS_DIR):
    all_valid = True
    for path in root_path.glob('**/*.po'):
        if invalid := _get_invalid_po_format_strings(path):
            all_valid = False
            click.echo(f'Found invalid format strings in {path.relative_to(root_path)}')
            for item in invalid:
                click.echo(cformat('%{yellow}{}%{reset} | %{yellow!}{}%{reset}\n%{red}{}%{reset} != %{red!}{}%{reset}')
                           .format(item['orig'], item['trans'],
                                   list(item['orig_placeholders']), list(item['trans_placeholders'])))
            click.echo()
    return all_valid


def _check_mismatched_html_tags(root_path: Path = TRANSLATIONS_DIR):
    all_valid = True
    for path in root_path.glob('**/*.po'):
        if invalid := _get_mismatched_html_tags(path):
            all_valid = False
            click.echo(f'Found mismatched HTML tags in {path.relative_to(root_path)}')
            for item in invalid:
                click.echo(cformat('%{yellow}{}%{reset} | %{yellow!}{}%{reset}\n%{red}{}%{reset} != %{red!}{}%{reset}')
                           .format(item['orig'], item['trans'], list(item['orig_tags']), list(item['trans_tags'])))
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


@cli.command()
def check_html_tags():
    """Check whether the HTML tags in the source and the translated message match.

    This helps find cases where e.g. the translated message does not properly
    close the tags. Additionally, this ensures that no one sneaks in dangerous
    HTML (like a <script> tag) into the translations.
    """
    if all_valid := _check_mismatched_html_tags():
        click.secho('No issues found!', fg='green', bold=True)
    sys.exit(0 if all_valid else 1)


def _extract_placeholders(string):
    pattern = r'''(
        \{[^}]*\}    # Match closing curly brace (incl. empty)
        |            # OR
        \%\([^)]+\)  # Match closing parenthesis
        [sdf]        # Match format type (string, decimal, float)
    )
    '''
    return set(re.findall(pattern, string, re.VERBOSE))


def _get_invalid_po_format_strings(path):
    with open(path, 'rb') as f:
        catalog = read_po(f)

    invalid = []
    for msg_pairs in _iter_msg_pairs(catalog):
        for orig, trans in msg_pairs:
            orig_placeholders = _extract_placeholders(orig)
            trans_placeholders = _extract_placeholders(trans)
            if orig_placeholders != trans_placeholders:
                invalid.append({
                    'orig': orig,
                    'trans': trans,
                    'orig_placeholders': orig_placeholders,
                    'trans_placeholders': trans_placeholders
                })
    return invalid


def _get_mismatched_html_tags(path):
    with open(path, 'rb') as f:
        catalog = read_po(f)

    mismatched = []
    for msg_pairs in _iter_msg_pairs(catalog):
        for orig, trans in msg_pairs:
            if not orig:  # Ignore the empty message
                continue

            orig_tags = sorted(re.findall(r'<[^>]+>', orig))
            trans_tags = sorted(re.findall(r'<[^>]+>', trans))

            # Ignore line breaks
            orig_tags = [tag for tag in orig_tags if tag != '<br>']
            trans_tags = [tag for tag in trans_tags if tag != '<br>']

            if orig_tags != trans_tags:
                mismatched.append({
                    'orig': orig,
                    'trans': trans,
                    'orig_tags': orig_tags,
                    'trans_tags': trans_tags
                })

    return mismatched


def _iter_msg_pairs(catalog):
    """Iterate over all (original, translated) message pairs in the catalog.

    For singular messages, this produces a single pair (original, translated).
    For plural messages, this produces a pair for each plural form. For example,
    for a language with 4 plural forms, this will generate:

        (orig_singular, trans_singular),
        (orig_plural,   trans_plural_1),
        (orig_plural,   trans_plural_2),
        (orig_plural,   trans_plural_3)

    For languages with nplurals=1, this generates a single pair:

        (orig_plural, trans_plural)
    """
    for msg in catalog:
        all_trans = msg.string if isinstance(msg.string, tuple) else (msg.string,)
        if not any(all_trans):  # not translated
            continue

        if not msg.pluralizable:
            yield ((msg.id, msg.string),)
        elif catalog.num_plurals == 1:
            # Pluralized messages with nplurals=1 should be compared against the 'msgid_plural'
            yield ((msg.id[1], msg.string[0]),)
        else:
            # Pluralized messages with nplurals>1 should compare 'msgstr[0]' against the singular and
            # any other 'msgstr[X]' against 'msgid_plural'.
            yield ((msg.id[0], msg.string[0]), *((msg.id[1], t) for t in msg.string[1:]))
