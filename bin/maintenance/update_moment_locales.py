#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

"""Keep moment.js locales in sync with 'indico/translations'.

This updates the 'indico/web/client/js/jquery/index.js' file to
include all moment.js locales corresponding to those in 'indico/translations'.
"""

import difflib
import re
import sys
from pathlib import Path

import click
import yaml
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.diff import DiffLexer


START_MARKER = '// moment.js locales'
END_MARKER = '// Last imported locale is used as fallback'


def _format_import(locale):
    return f"import 'moment/locale/{locale}';"


def generate_locale_imports(locale_dir, locale_mapping):
    """Generate moment.js import statements for locales in 'indico/translations'.

    'en_US' is skipped as it is not the default moment locale. 'en_GB' is skipped as
    it is already included as the fallback locale in 'indico/web/client/js/jquery/index.js'.
    """
    imports = []

    for locale in locale_dir.iterdir():
        if locale.is_dir() and locale.stem not in {'en_US', 'en_GB'}:
            # moment.js does not use canonical locales names, so we use the mapping from
            # 'moment_locales.yaml' to get the correct name
            moment_locale = locale_mapping[locale.stem]
            imports.append(_format_import(moment_locale))

    return '\n'.join(sorted(imports))


def show_diff(old, new, filename):
    diff = difflib.unified_diff(old.splitlines(), new.splitlines(), filename, filename, lineterm='')
    diff = '\n'.join(diff)
    print(highlight(diff, DiffLexer(), Terminal256Formatter(style='native')))


@click.command()
@click.option('--ci', is_flag=True, help='Indicate that the script is running during CI and should use a non-zero '
                                         'exit code if thefile is not up to date instead of updating it.')
def main(ci):
    indico_root = Path(__file__).parents[2]

    locale_mapping_file = indico_root / 'indico' / 'moment_locales.yaml'
    locale_mappings = yaml.safe_load(locale_mapping_file.read_text())
    locale_dir = indico_root / 'indico' / 'translations'
    locale_imports = generate_locale_imports(locale_dir, locale_mappings)

    index_path = indico_root / 'indico' / 'web' / 'client' / 'js' / 'jquery' / 'index.js'
    index_path_pretty = index_path.relative_to(indico_root)

    replaced = False

    def replacer(_):
        nonlocal replaced
        replaced = True
        return locale_imports

    old_file_content = index_path.read_text()
    new_file_content = re.sub(fr'(?<={re.escape(START_MARKER)}\n).*(?=\n{re.escape(END_MARKER)})',
                              replacer, old_file_content, flags=re.DOTALL)

    if not replaced:
        click.secho(f'Failed to patch {index_path_pretty}', fg='red')
        sys.exit(1)

    if old_file_content == new_file_content:
        click.secho(f'{index_path_pretty} is up to date', fg='green')
        sys.exit(0)

    if ci:
        click.secho(f'{index_path_pretty} is not up to date:', fg='red')
        show_diff(old_file_content, new_file_content, str(index_path_pretty))
        sys.exit(1)

    index_path.write_text(new_file_content)
    click.secho(f'Updated {index_path_pretty}:', fg='yellow')
    show_diff(old_file_content, new_file_content, str(index_path_pretty))


if __name__ == '__main__':
    main()
