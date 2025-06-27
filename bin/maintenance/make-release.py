#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import difflib
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import click
import dateutil.parser
from babel.dates import format_date
from dateutil.relativedelta import relativedelta
from packaging.version import Version
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.diff import DiffLexer
from terminaltables import GithubFlavoredMarkdownTable


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

VERSIONS_SECTION_PATTERN = r'^([\s\S]*^<!-- VERSIONS .* -->)($[\s\S]+)([\n\r]+^<!-- ENDVERSIONS -->$[\s\S]*)$'


def fail(message, *args, **kwargs):
    click.echo(click.style('Error: ' + message.format(*args), fg='red', bold=True), err=True)
    if 'verbose_msg' in kwargs:
        click.echo(kwargs['verbose_msg'], err=True)
    sys.exit(1)


def warn(message, *args):
    click.echo(click.style(message.format(*args), fg='yellow', bold=True), err=True)


def info(message, *args):
    click.echo(click.style(message.format(*args), fg='green', bold=True), err=True)


def step(message, *args, **kwargs):
    dry_run = kwargs.get('dry_run')
    suffix = click.style(' (not really due to dry-run)', fg='yellow', bold=False) if dry_run else ''
    click.echo(click.style(message.format(*args) + suffix, fg='white', bold=True), err=True)


def _bump_version(version):
    try:
        parts = [int(v) for v in version.split('.')]
    except ValueError:
        fail('cannot bump version with non-numeric parts')
    if len(parts) == 2:
        parts.append(0)
    parts[-1] += 1
    return '.'.join(map(str, parts))


def _get_current_version():
    content = Path('indico/__init__.py').read_text()
    match = re.search(r"^__version__ = '([^']+)'$", content, re.MULTILINE)
    return match.group(1)


def _set_version(version, dry_run=False):
    step('Setting version to {}', version, dry_run=dry_run)
    init_py = Path('indico/__init__.py')
    orig = content = init_py.read_text()
    content = re.sub(r"^__version__ = '([^']+)'$", f"__version__ = '{version}'", content, flags=re.MULTILINE)
    assert content != orig
    if not dry_run:
        init_py.write_text(content)


def _set_changelog_date(new_version, dry_run=False):
    changes_rst = Path('CHANGES.rst')
    orig = content = changes_rst.read_text()
    version_line = f'Version {new_version}'
    underline = '-' * len(version_line)
    unreleased = re.escape('Unreleased')
    release_date = format_date(format='MMMM dd, yyyy', locale='en')
    content = re.sub(fr'(?<={re.escape(version_line)}\n{underline}\n\n\*){unreleased}(?=\*\n)',
                     f'Released on {release_date}',
                     content,
                     flags=re.DOTALL)
    step('Setting release date to {}', release_date, dry_run=dry_run)
    if content == orig:
        fail('Could not update changelog - is there an entry for {}?', new_version)
    if not dry_run:
        changes_rst.write_text(content)


def _canonicalize_version(new_version):
    version = Version(new_version)
    if len(version._version.release) == 3 and version._version.release[-1] == 0:
        warn('Removing trailing `.0` from {}', new_version)
        new_version = '.'.join(map(str, version._version.release[:-1]))
    return new_version


def _get_versions(version):
    cur_version = _get_current_version()
    new_version = _canonicalize_version(version or cur_version.replace('-dev', ''))
    pre = not all(x.isdigit() for x in new_version.split('.'))
    if cur_version == new_version:
        fail('Version number did not change',
             verbose_msg=('During alpha/beta/rc you need to specify the new version manually' if pre else None))
    next_version = (_bump_version(new_version) + '-dev') if not pre else None
    return cur_version, new_version, next_version


def _tag_name(version):
    return 'v' + version


def _check_tag(version):
    tag_name = _tag_name(version)
    if tag_name in subprocess.check_output(['git', 'tag'], encoding='utf-8').splitlines():
        fail('Git tag already exists: {}', tag_name)


def _check_git_clean():
    cmds = [['git', 'diff', '--stat', '--color=always'],
            ['git', 'diff', '--stat', '--color=always', '--staged']]
    for cmd in cmds:
        rv = subprocess.check_output(cmd, stderr=subprocess.STDOUT, encoding='utf-8')
        if rv:
            fail('Git working tree is not clean', verbose_msg=rv)


def _git_commit(message, files, dry_run=False):
    step("Committing '{}'", message, dry_run=dry_run)
    if dry_run:
        return
    subprocess.check_call(['git', 'add', *files])
    subprocess.check_call(['git', 'commit', '--no-verify', '--message', message])


def _git_tag(version, message, sign, dry_run):
    tag_name = _tag_name(version)
    step('Tagging {}', tag_name, dry_run=dry_run)
    if dry_run:
        return
    sign_args = ['--sign'] if sign else []
    subprocess.check_call(['git', 'tag', '--message', message, tag_name, *sign_args])


def _build_wheel(no_assets, dry_run):
    step('Building wheel', dry_run=dry_run)
    if dry_run:
        return
    args = ['--no-assets'] if no_assets else []
    subprocess.check_call(['./bin/maintenance/build-wheel.py', 'indico', *args])


def _create_changelog_stub(released_version, next_version, *, dry_run=False):
    changes_rst = Path('CHANGES.rst')
    content = changes_rst.read_text()
    released_version_line = f'Version {released_version}'
    version_line = f'Version {next_version}'
    underline = '-' * len(version_line)
    stub = CHANGELOG_STUB.format(version_line=version_line, underline=underline)
    if version_line in content:
        warn('Changelog entry for {} already exists, not creating stub', next_version)
        return
    pos = content.index(released_version_line)
    content = content[:pos] + stub + content[pos:]
    step('Creating changelog stub for {}', next_version, dry_run=dry_run)
    if not dry_run:
        changes_rst.write_text(content)


def _parse_changelog_versions() -> list[tuple[str, date]]:
    """Retrieve versions from the changelog file."""
    return [(v, dateutil.parser.parse(d).date()) for v, d in re.findall(
        r'^Version ([0-9.abrc]+)\n-+\n\n\*Released on (.+)\*\n$',
        Path('CHANGES.rst').read_text(),
        re.MULTILINE,
    )]


def _replace_auto_section(content: str, new_table: str) -> str:
    """Replace content within the VERSIONS_SECTION_PATTERN markers."""
    if match := re.search(VERSIONS_SECTION_PATTERN, content, re.MULTILINE):
        return f'{match.group(1)}\n{new_table}{match.group(3)}'
    raise ValueError('Could not find VERSIONS section markers in SECURITY.md')


def _show_diff(old: str, new: str, filename: str):
    diff = difflib.unified_diff(old.splitlines(), new.splitlines(), filename, filename, lineterm='')
    diff = '\n'.join(diff)
    print(highlight(diff, DiffLexer(), Terminal256Formatter(style='native')))


def _update_security_md(*, dry_run: bool = False):
    """Update the SECURITY.md file with the new supported version information."""
    security_md = Path('SECURITY.md')
    content = security_md.read_text()
    versions = _parse_changelog_versions()

    # find the date of the first release of the current minor version,
    # as well as the last release of the previous minor version
    minor_releases = [(version, release_date) for version, release_date in versions if not Version(version).micro]
    latest_minor_version, latest_minor_version_date = minor_releases[0]
    prev_minor_release = minor_releases[1][0]

    # 4 months after the first minor version of the current release
    deadline = latest_minor_version_date + relativedelta(months=4)
    deadline_txt = format_date(deadline, format='medium', locale='en')

    support_text = (
        f'❌ No (ended {deadline_txt})'
        if date.today() > deadline
        else f'🚑 Limited (until {deadline_txt})'
    )

    new_table = GithubFlavoredMarkdownTable(
        [
            ['Version', 'Supported'],
            [f'{latest_minor_version}.x', '✅ Yes (latest version)'],
            [f'{prev_minor_release}.x', support_text],
            ['Others', '❌ No'],
        ]
    ).table

    # Replace auto-generated section
    updated_content = _replace_auto_section(content, new_table)
    if content == updated_content:
        return

    if dry_run:
        _show_diff(content, updated_content, security_md.name)
    else:
        security_md.write_text(updated_content)


@click.command()
@click.argument('version', required=False)
@click.option('--dry-run', '-n', is_flag=True, help='Do not modify any files or run commands')
@click.option('--sign', '-s', is_flag=True, help='Sign the Git commit/tag with GPG')
@click.option('--no-assets', '-D', is_flag=True, help='Skip building assets when building the wheel')
@click.option('--no-changelog', '-C', is_flag=True, help='Do not update the date in the changelog')
@click.option('--next-changelog', '-N', is_flag=True, help='Add changelog stub for next version')
def cli(version, dry_run, sign, no_assets, no_changelog, next_changelog):
    os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))
    cur_version, new_version, next_version = _get_versions(version)
    _check_tag(new_version)
    if next_version:
        _check_tag(next_version)
    elif next_changelog:
        fail('Next version unknown, cannot generate changelog stub')
    _check_git_clean()
    info('Current version is {}', cur_version)
    info('Going to release {}', new_version)
    if next_version:
        info('Next version will be {}', next_version)
    if not no_changelog:
        _set_changelog_date(new_version, dry_run=dry_run)
    _update_security_md(dry_run=dry_run)
    _set_version(new_version, dry_run=dry_run)
    release_msg = f'Release {new_version}'
    _git_commit(release_msg, ['SECURITY.md', 'CHANGES.rst', 'indico/__init__.py'], dry_run=dry_run)
    _git_tag(new_version, release_msg, sign=sign, dry_run=dry_run)
    prompt = 'Build release wheel before bumping version?' if next_version else 'Build release wheel now?'
    if click.confirm(click.style(prompt, fg='blue', bold=True), default=False):
        _build_wheel(no_assets, dry_run=dry_run)
    if next_version:
        next_message = f'Bump version to {next_version}'
        _set_version(next_version, dry_run=dry_run)
        _git_commit(next_message, ['indico/__init__.py'], dry_run=dry_run)
    if next_changelog:
        next_release_version = next_version.replace('-dev', '')
        _create_changelog_stub(new_version, next_release_version, dry_run=dry_run)
        _git_commit(f'Add {next_release_version} changelog stub', ['CHANGES.rst'], dry_run=dry_run)


if __name__ == '__main__':
    cli()
