#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

"""Patch Indico to include all moment.js locales.

This updates the 'indico/web/client/js/jquery/index.js' file to
include all moment.js locales from 'node_modules/moment/locale'.
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
def main():
    indico_root = Path(__file__).parents[2]

    locale_mapping_file = indico_root / 'indico' / 'moment_locales.yaml'
    locale_mappings = yaml.safe_load(locale_mapping_file.read_text())
    locale_dir = indico_root / 'indico' / 'translations'
    locale_imports = generate_locale_imports(locale_dir, locale_mappings)

    index_path = indico_root / 'indico' / 'web' / 'client' / 'js' / 'jquery' / 'index.js'
    index_path_pretty = index_path.relative_to(indico_root)

    old_index_file = index_path.read_text()
    new_index_file = re.sub(fr'(?<={re.escape(START_MARKER)}\n).*(?=\n{re.escape(END_MARKER)})',
                            lambda __: locale_imports, old_index_file, flags=re.DOTALL)

    if new_index_file == old_index_file:
        click.secho(f'Failed to patch {index_path_pretty}', fg='red')
        sys.exit(1)

    index_path.write_text(new_index_file)
    click.secho(f'Updated {index_path_pretty}:', fg='yellow')
    show_diff(old_index_file, new_index_file, str(index_path_pretty))


if __name__ == '__main__':
    main()
