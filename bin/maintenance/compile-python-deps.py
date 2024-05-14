#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import itertools
import subprocess
import sys

import click


COMMANDS = {
    'main': ('uv', 'pip', 'compile', 'requirements.in', '-o', 'requirements.txt'),
    'dev': ('uv', 'pip', 'compile', 'requirements.dev.in', '-o', 'requirements.dev.txt'),
    'docs': ('uv', 'pip', 'compile', 'docs/requirements.in', '-o', 'docs/requirements.txt'),
}


@click.command()
@click.option('-U', '--upgrade', is_flag=True, help='Upgrade all packages')
@click.option('-P', '--upgrade-package', 'upgrade_packages', multiple=True, help='Upgrade the specified packages')
def main(upgrade, upgrade_packages):
    """Compiles/upgrades the transitive Python dependencies.

    This tool is a simple wrapper for `uv pip compile` that handles all the
    separate requirements files automatically.
    """
    if upgrade and upgrade_packages:
        raise click.UsageError('When upgrading all packages it makes no sense to specify package names')

    args = (
        '--custom-compile-command',
        './bin/maintenance/compile-python-deps.py',
        '--no-emit-package',
        'setuptools',
    )
    if upgrade:
        args += ('-U',)
    elif upgrade_packages:
        args += tuple(itertools.chain.from_iterable(('-P', pkg) for pkg in upgrade_packages))

    failed = False
    for name, command in COMMANDS.items():
        click.echo(f'Compiling {click.style(name, bold=True)} deps')
        proc = subprocess.run([*command, *args], stdout=subprocess.DEVNULL)
        if proc.returncode:
            failed = True

    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
