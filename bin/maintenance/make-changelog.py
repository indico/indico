#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
import subprocess
import sys
from pathlib import Path

import click
from packaging.version import Version


CHANGELOG_STUB = '''
{version_line}
{underline}

*Unreleased*

Improvements
^^^^^^^^^^^^

- Nothing so far :(

Bugfixes
^^^^^^^^

- Nothing so far :)

Accessibility
^^^^^^^^^^^^^

- Nothing so far

Internal Changes
^^^^^^^^^^^^^^^^

- Nothing so far


'''.lstrip()


CHANGELOG_MAJOR_STUB = '''
{version_line}
{underline}

*Unreleased*

Major Features
^^^^^^^^^^^^^^

- Nothing so far

Internationalization
^^^^^^^^^^^^^^^^^^^^

- Nothing so far

Improvements
^^^^^^^^^^^^

- Nothing so far

Bugfixes
^^^^^^^^

- Nothing so far

Accessibility
^^^^^^^^^^^^^

- Nothing so far

Internal Changes
^^^^^^^^^^^^^^^^

- Nothing so far


----


'''.lstrip()


def step(message, *args):
    click.echo(click.style(message.format(*args), fg='white', bold=True), err=True)


def fail(message, *args):
    click.echo(click.style('Error: ' + message.format(*args), fg='red', bold=True), err=True)
    sys.exit(1)


def _git_diff(file):
    subprocess.call(['git', 'diff', '--', file])


def _git_commit(message, files):
    step("Committing '{}'", message)
    subprocess.check_call(['git', 'add', *files])
    subprocess.check_call(['git', 'commit', '--no-verify', '--message', message])


def _create_changelog_stub(version):
    changes_rst = Path('CHANGES.rst')
    content = changes_rst.read_text()
    latest_version_re = r'^Version ([0-9.abrc]+)\n-{9,}\n\n\*(Unreleased|Released on .+)\*\n'
    version_line = f'Version {version}'
    underline = '-' * len(version_line)
    if version_line in content:
        fail('Changelog entry for {} already exists, cannot create new stub', version)
    if not (match := re.search(latest_version_re, content, re.MULTILINE)):
        fail('Could not find latest release')
    latest_version = Version(match.group(1))
    version = Version(version)
    if latest_version >= version:
        fail('New version {} seems older than current latest version {}', version, latest_version)
    pos = match.start()
    major = latest_version.release[:2] != version.release[:2]  # e.g. 3.2 to 3.3
    template = CHANGELOG_MAJOR_STUB if major else CHANGELOG_STUB
    stub = template.format(version_line=version_line, underline=underline)
    content = content[:pos] + stub + content[pos:]
    step('Creating changelog stub for {}', version)
    changes_rst.write_text(content)


@click.command()
@click.argument('version', required=True)
def cli(version):
    _create_changelog_stub(version)
    _git_diff('CHANGES.rst')
    prompt = 'Commit changelog stub now?'
    if click.confirm(click.style(prompt, fg='blue', bold=True), default=True):
        _git_commit(f'Add {version} changelog stub', ['CHANGES.rst'])


if __name__ == '__main__':
    cli()
