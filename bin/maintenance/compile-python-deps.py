#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import difflib
import itertools
import subprocess
import sys
from pathlib import Path

import click
import tomlkit
from hatch_requirements_txt import load_requirements_files
from packaging.requirements import Requirement
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.diff import DiffLexer


COMMANDS = {
    'main': ('uv', 'pip', 'compile', 'requirements.in', '-o', 'requirements.txt'),
    'dev': ('uv', 'pip', 'compile', 'requirements.dev.in', '-o', 'requirements.dev.txt'),
    'docs': ('uv', 'pip', 'compile', 'docs/requirements.in', '-o', 'docs/requirements.txt'),
}


def _show_diff(old, new, filename):
    diff = difflib.unified_diff(old.splitlines(), new.splitlines(), filename, filename, lineterm='')
    diff = '\n'.join(diff)
    print(highlight(diff, DiffLexer(), Terminal256Formatter(style='native')))


def _update_pyproject_reqs(data, context):
    reqs = {x.name: str(x) for x in load_requirements_files(['requirements.txt'])[0]}
    reqs |= {x.name: str(x) for x in load_requirements_files(['requirements.dev.txt'])[0]}
    for getter in (
        lambda: data['build-system']['requires'],
        lambda: data['tool']['hatch']['build']['targets']['sdist']['hooks']['custom']['dependencies'],
    ):
        try:
            deplist = getter()
        except KeyError:
            continue
        for i, req in enumerate(deplist):
            req_name = Requirement(req).name
            try:
                new_req = reqs[req_name]
            except KeyError:
                print(f'[{context}] Requirement {req_name} not pinned in Indico core')
                continue
            deplist[i] = tomlkit.string(new_req, literal=True)


def _update_pyproject(pyproject_path: Path, context: str):
    old_content = pyproject_path.read_text()
    data = tomlkit.parse(old_content)
    _update_pyproject_reqs(data, context)
    new_content = tomlkit.dumps(data)
    if old_content != new_content:
        _show_diff(old_content, new_content, str(pyproject_path))
        pyproject_path.write_text(new_content)


@click.command()
@click.option('-U', '--upgrade', is_flag=True, help='Upgrade all packages')
@click.option('-P', '--upgrade-package', 'upgrade_packages', multiple=True, help='Upgrade the specified packages')
@click.option('-N', '--no-plugins', is_flag=True, help='Do not touch plugin pyproject.toml files')
def main(upgrade, upgrade_packages, no_plugins):
    """Compiles/upgrades the transitive Python dependencies.

    This tool is a simple wrapper for `uv pip compile` that handles all the
    separate requirements files automatically.
    """
    if upgrade and upgrade_packages:
        raise click.UsageError('When upgrading all packages it makes no sense to specify package names')

    args = (
        '--custom-compile-command',
        './bin/maintenance/compile-python-deps.py',
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

    _update_pyproject(Path('pyproject.toml'), 'Indico')
    if not no_plugins:
        for plugin_pyproject in Path('../plugins').glob('**/pyproject.toml'):
            _update_pyproject(plugin_pyproject, plugin_pyproject.parent.name)

    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
