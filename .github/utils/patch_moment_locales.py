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
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.diff import DiffLexer


START_MARKER = '// moment.js locales'
END_MARKER = '// Last imported locale is used as fallback'


def _format_import(locale):
    return f"import 'moment/locale/{locale}';"


def generate_locale_imports(indico_root):
    locales = indico_root / 'node_modules' / 'moment' / 'locale'
    for locale in sorted(locales.glob('*.js')):
        if locale.stem != 'en-gb':
            yield _format_import(locale.stem)


def show_diff(old, new, filename):
    diff = difflib.unified_diff(old.splitlines(), new.splitlines(), filename, filename, lineterm='')
    diff = '\n'.join(diff)
    print(highlight(diff, DiffLexer(), Terminal256Formatter(style='native')))


@click.command()
def main():
    indico_root = Path(__file__).parents[2]
    locale_imports = '\n'.join(generate_locale_imports(indico_root))
    index_path = indico_root / 'indico' / 'web' / 'client' / 'js' / 'jquery' / 'index.js'
    index_path_pretty = index_path.relative_to(indico_root)

    old_file = index_path.read_text()
    new_file = re.sub(fr'(?<={re.escape(START_MARKER)}\n).*(?=\n{re.escape(END_MARKER)})', lambda __: locale_imports,
                      old_file, flags=re.DOTALL)

    if new_file == old_file:
        click.secho(f'Failed to patch {index_path_pretty}', fg='red')
        sys.exit(1)

    index_path.write_text(new_file)
    click.secho(f'Updated {index_path_pretty}:', fg='yellow')
    show_diff(old_file, new_file, str(index_path_pretty))


if __name__ == '__main__':
    main()
