#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
from pathlib import Path

import click
import yaml


HEADER = '''
# This file provides a mapping between the canonical locale names and
# locale names used by moment.js.
#
# Moment locale names are all lowercase separated by a dash(-) e.g. 'en_CA' becomes 'en-ca'.
# Moment also tends to only use the language code for single-country locales e.g. fr_FR -> fr, cs_CZ -> cs.
#
# Two sources for the canonical names were used:
# - Unicode CLDR (https://cldr.unicode.org/)
# - glibc locales (with locale modifiers removed)
#
# These were merged together and the corresponding moment locale was found.
# If an exact match didn't exist a match with the script and/or territory removed was used.
# Some of the moment.js locales do not exist in either of the sources listed above.
# These are:
# {unmatched_locales}
#
# These should however be fairly uncommon.
#
# Generated using moment version: {moment_version}
#
'''.lstrip()


USAGE = '''
Generates a mapping table between canonical locale identifiers and identifiers
used by moment.js. This is needed because moment uses a different naming convention
incompatible with the official identifiers and with the identifiers provided by browsers.
See the the generated file header for more information.

The list of moment locales is read from the current version of moment installed
in Indico's node_modules directory.

You can specify the output file:

    ./bin/maintenance/generate_moment_locales.py -o moment_locales.yaml

The generated file should be placed in the Indico root directory (which is done
by default).
'''


def load_canonical_locales():
    path = Path(__file__).parent / 'canonical_locales.yaml'
    return yaml.safe_load(path.read_text())


def load_moment_locales():
    path = Path(__file__).parent / '../../node_modules/moment/dist/locale'
    files = path.glob('*.js')
    return [file.stem for file in files] + ['en']


def get_moment_version():
    path = Path(__file__).parent / '../../node_modules/moment/package.json'
    return json.loads(path.read_text())['version']


def to_moment(locale):
    parts = locale.lower().split('_')
    return f'{parts[0]}-{parts[-1]}'


@click.command(help=USAGE)
@click.option('--output', '-o', type=click.Path(path_type=Path), default='indico/moment_locales.yaml',
              help='Output file')
def generate(output: Path):
    canonical = load_canonical_locales()
    moment = load_moment_locales()
    moment_version = get_moment_version()

    table = {}
    for locale in canonical:
        moment_locale = to_moment(locale)
        language = moment_locale.split('-')[0]
        if moment_locale in moment:
            table[locale] = moment_locale
        elif language in moment:
            table[locale] = language

    unmatched_locales = sorted(set(moment) - set(table.values()))
    click.secho('Locales generated.', fg='green', bold=True)
    click.secho('Unmatched moment locales:', fg='yellow')
    click.echo(json.dumps(unmatched_locales, indent=2))

    header = HEADER.format(unmatched_locales=unmatched_locales, moment_version=moment_version)
    locales = yaml.safe_dump(table)
    output.write_text(header + locales)


if __name__ == '__main__':
    generate()
