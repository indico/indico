#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import difflib
import json
import re
import sys
from pathlib import Path

import click
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.diff import DiffLexer


START_MARKER = '// BEGIN GENERATED ICON RULES'
END_MARKER = '// END GENERATED ICON RULES'
RULE_TEMPLATE = '''
.icon-{name}::before,
%icon-{name} {{
  content: '\\{code:x}';
}}
'''.strip()


def generate_icon_rules(selection_file):
    """Generate SCSS rules from the icomoon selection.json file."""
    # Read the selection file and get the icon names
    selection = json.loads(selection_file.read_text())
    icons = sorted(
        (
            icon['properties']['name'].split(',', 1)[0].lower().replace('_', '-'),
            icon['properties']['code']
        )
        for icon in selection['icons']
    )

    # Generate the icon list
    return '\n'.join(RULE_TEMPLATE.format(name=icon[0], code=icon[1]) for icon in icons)


def show_diff(old, new, filename):
    diff = difflib.unified_diff(old.splitlines(), new.splitlines(), filename, filename, lineterm='')
    diff = '\n'.join(diff)
    print(highlight(diff, DiffLexer(), Terminal256Formatter(style='native')))


@click.command()
@click.option('--ci', is_flag=True, help='Indicate that the script is running during CI and should use a non-zero '
                                         'exit code if any files are not up to date.')
def main(ci):
    indico_root = Path(__file__).parents[2]
    web_dir = indico_root / 'indico' / 'web'
    selection_file = web_dir / 'static' / 'fonts' / 'icomoon' / 'selection.json'
    stylesheet_file = web_dir / 'client' / 'styles' / 'partials' / '_icons.scss'
    stylesheet_file_pretty = stylesheet_file.relative_to(Path.cwd())

    rules = generate_icon_rules(selection_file)

    # Generate the final SCSS file
    old_stylesheet = stylesheet_file.read_text()
    new_stylesheet = re.sub(fr'(?<={re.escape(START_MARKER)}\n).*(?=\n{re.escape(END_MARKER)})', lambda __: rules,
                            old_stylesheet, flags=re.DOTALL)

    if new_stylesheet == old_stylesheet:
        click.secho(f'{stylesheet_file_pretty} is up to date', fg='green')
        sys.exit(0)

    if ci:
        click.secho(f'{stylesheet_file_pretty} is not up to date:', fg='red')
        show_diff(old_stylesheet, new_stylesheet, str(stylesheet_file_pretty))
        sys.exit(1)

    stylesheet_file.write_text(new_stylesheet)
    click.secho(f'Updated {stylesheet_file_pretty}:', fg='yellow')
    show_diff(old_stylesheet, new_stylesheet, str(stylesheet_file_pretty))


if __name__ == '__main__':
    main()
