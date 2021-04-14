#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import re
import subprocess
import sys

import click
from babel.dates import format_date
from packaging.version import Version


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


def run(cmd, title, shell=False):
    if shell:
        cmd = ' '.join(cmd)
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=shell)
    except subprocess.CalledProcessError as exc:
        fail(f'{title} failed', verbose_msg=exc.output)


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
    with open('indico/__init__.py') as f:
        content = f.read()
    match = re.search(r"^__version__ = '([^']+)'$", content, re.MULTILINE)
    return match.group(1)


def _set_version(version, dry_run=False):
    step('Setting version to {}', version, dry_run=dry_run)
    with open('indico/__init__.py') as f:
        orig = content = f.read()
    content = re.sub(r"^__version__ = '([^']+)'$", f"__version__ = '{version}'", content, flags=re.MULTILINE)
    assert content != orig
    if not dry_run:
        with open('indico/__init__.py', 'w') as f:
            f.write(content)


def _set_changelog_date(new_version, dry_run=False):
    with open('CHANGES.rst') as f:
        orig = content = f.read()
    version_line = f'Version {new_version}'
    underline = '-' * len(version_line)
    unreleased = re.escape('Unreleased')
    release_date = format_date(format='MMMM dd, YYYY', locale='en')
    content = re.sub(r'(?<={}\n{}\n\n\*){}(?=\*\n)'.format(re.escape(version_line), underline, unreleased),
                     f'Released on {release_date}',
                     content,
                     flags=re.DOTALL)
    step('Setting release date to {}', release_date, dry_run=dry_run)
    if content == orig:
        fail('Could not update changelog - is there an entry for {}?', new_version)
    if not dry_run:
        with open('CHANGES.rst', 'w') as f:
            f.write(content)


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
    if tag_name in subprocess.check_output(['git', 'tag']).splitlines():
        fail('Git tag already exists: {}', tag_name)


def _check_git_clean():
    cmds = [['git', 'diff', '--stat', '--color=always'],
            ['git', 'diff', '--stat', '--color=always', '--staged']]
    for cmd in cmds:
        rv = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        if rv:
            fail('Git working tree is not clean', verbose_msg=rv)


def _git_commit(message, files, dry_run=False):
    step("Committing '{}'", message, dry_run=dry_run)
    if dry_run:
        return
    subprocess.check_call(['git', 'add'] + files)
    subprocess.check_call(['git', 'commit', '--no-verify', '--message', message])


def _git_tag(version, message, sign, dry_run):
    tag_name = _tag_name(version)
    step('Tagging {}', tag_name, dry_run=dry_run)
    if dry_run:
        return
    sign_args = ['--sign'] if sign else []
    subprocess.check_call(['git', 'tag', '--message', message, tag_name] + sign_args)


def _build_wheel(no_assets, dry_run):
    step("Building wheel", dry_run=dry_run)
    if dry_run:
        return
    args = ['--no-assets'] if no_assets else []
    subprocess.check_call(['./bin/maintenance/build-wheel.py', 'indico'] + args)


@click.command()
@click.argument('version', required=False)
@click.option('--dry-run', '-n', is_flag=True, help='Do not modify any files or run commands')
@click.option('--sign', '-s', is_flag=True, help='Sign the Git commit/tag with GPG')
@click.option('--no-assets', '-D', is_flag=True, help='Skip building assets when building the wheel')
@click.option('--no-changelog', '-C', is_flag=True, help='Do not update the date in the changelog')
def cli(version, dry_run, sign, no_assets, no_changelog):
    os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))
    cur_version, new_version, next_version = _get_versions(version)
    _check_tag(new_version)
    if next_version:
        _check_tag(next_version)
    _check_git_clean()
    info('Current version is {}', cur_version)
    info('Going to release {}', new_version)
    if next_version:
        info('Next version will be {}', next_version)
    if not no_changelog:
        _set_changelog_date(new_version, dry_run=dry_run)
    _set_version(new_version, dry_run=dry_run)
    release_msg = f'Release {new_version}'
    _git_commit(release_msg, ['CHANGES.rst', 'indico/__init__.py'], dry_run=dry_run)
    _git_tag(new_version, release_msg, sign=sign, dry_run=dry_run)
    prompt = 'Build release wheel before bumping version?' if next_version else 'Build release wheel now?'
    if click.confirm(click.style(prompt, fg='blue', bold=True), default=True):
        _build_wheel(no_assets, dry_run=dry_run)
    if next_version:
        next_message = f'Bump version to {next_version}'
        _set_version(next_version, dry_run=dry_run)
        _git_commit(next_message, ['indico/__init__.py'], dry_run=dry_run)


if __name__ == '__main__':
    cli()
