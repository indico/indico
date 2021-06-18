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
from datetime import date

import click
import yaml

from indico.util.console import cformat


# Dictionary listing the files for which to change the header.
# The key is the extension of the file (without the dot) and the value is another
# dictionary containing two keys:
#   - 'regex' : A regular expression matching comments in the given file type
#   - 'format': A dictionary with the comment characters to add to the header.
#               There must be a `comment_start` inserted before the header,
#               `comment_middle` inserted at the beginning of each line except the
#               first and last one, and `comment_end` inserted at the end of the
#               header. (See the `HEADER` above)
SUPPORTED_FILES = {
    'py': {
        'regex': re.compile(r'((^#|[\r\n]#).*)*'),
        'format': {'comment_start': '#', 'comment_middle': '#', 'comment_end': ''}},
    'wsgi': {
        'regex': re.compile(r'((^#|[\r\n]#).*)*'),
        'format': {'comment_start': '#', 'comment_middle': '#', 'comment_end': ''}},
    'js': {
        'regex': re.compile(r'/\*(.|[\r\n])*?\*/|((^//|[\r\n]//).*)*'),
        'format': {'comment_start': '//', 'comment_middle': '//', 'comment_end': ''}},
    'jsx': {
        'regex': re.compile(r'/\*(.|[\r\n])*?\*/|((^//|[\r\n]//).*)*'),
        'format': {'comment_start': '//', 'comment_middle': '//', 'comment_end': ''}},
    'css': {
        'regex': re.compile(r'/\*(.|[\r\n])*?\*/'),
        'format': {'comment_start': '/*', 'comment_middle': ' *', 'comment_end': ' */'}},
    'scss': {
        'regex': re.compile(r'/\*(.|[\r\n])*?\*/|((^//|[\r\n]//).*)*'),
        'format': {'comment_start': '//', 'comment_middle': '//', 'comment_end': ''}},
}


# The substring which must be part of a comment block in order for the comment to be updated by the header.
SUBSTRING = 'This file is part of'


USAGE = '''
Updates all the headers in the supported files ({supported_files}).
By default, all the files tracked by git in the current repository are updated
to the current year.

You can specify a year to update to as well as a file or directory.
This will update all the supported files in the scope including those not tracked
by git. If the directory does not contain any supported files (or if the file
specified is not supported) nothing will be updated.
'''.format(supported_files=', '.join(SUPPORTED_FILES)).strip()


def _walk_to_root(path):
    """Yield directories starting from the given directory up to the root."""
    # Based on code from python-dotenv (BSD-licensed):
    # https://github.com/theskumar/python-dotenv/blob/e13d957b/src/dotenv/main.py#L245

    if os.path.isfile(path):
        path = os.path.dirname(path)

    last_dir = None
    current_dir = os.path.abspath(path)
    while last_dir != current_dir:
        yield current_dir
        parent_dir = os.path.abspath(os.path.join(current_dir, os.path.pardir))
        last_dir, current_dir = current_dir, parent_dir


def _get_config(path, end_year):
    config = {}
    for dirname in _walk_to_root(path):
        check_path = os.path.join(dirname, 'headers.yml')
        if os.path.isfile(check_path):
            with open(check_path) as f:
                config.update((k, v) for k, v in yaml.safe_load(f.read()).items() if k not in config)
            if config.pop('root', False):
                break

    if 'start_year' not in config:
        click.echo('no valid headers.yml files found: start_year missing')
        sys.exit(1)
    if 'name' not in config:
        click.echo('no valid headers.yml files found: name missing')
        sys.exit(1)
    if 'header' not in config:
        click.echo('no valid headers.yml files found: header missing')
        sys.exit(1)
    config['end_year'] = end_year
    return config


def gen_header(data):
    if data['start_year'] == data['end_year']:
        data['dates'] = data['start_year']
    else:
        data['dates'] = '{} - {}'.format(data['start_year'], data['end_year'])
    return '\n'.join(line.rstrip() for line in data['header'].format(**data).strip().splitlines())


def _update_header(file_path, config, substring, regex, data, ci):
    found = False
    with open(file_path) as file_read:
        content = orig_content = file_read.read()
        if not content.strip():
            return False
        shebang_line = None
        if content.startswith('#!/'):
            shebang_line, content = content.split('\n', 1)
        for match in regex.finditer(content):
            if substring in match.group():
                found = True
                content = content[:match.start()] + gen_header(data | config) + content[match.end():]
        if shebang_line:
            content = shebang_line + '\n' + content
    if content != orig_content:
        msg = 'Incorrect header in {}' if ci else cformat('%{green!}Updating header of %{blue!}{}')
        print(msg.format(os.path.relpath(file_path)))
        if not ci:
            with open(file_path, 'w') as file_write:
                file_write.write(content)
        return True
    elif not found:
        msg = 'Missing header in {}' if ci else cformat('%{red!}Missing header%{reset} in %{blue!}{}')
        print(msg.format(os.path.relpath(file_path)))
        return True


def update_header(file_path, year, ci):
    config = _get_config(file_path, year)
    ext = file_path.rsplit('.', 1)[-1]
    if ext not in SUPPORTED_FILES or not os.path.isfile(file_path):
        return False
    if os.path.basename(file_path)[0] == '.':
        return False
    return _update_header(file_path, config, SUBSTRING, SUPPORTED_FILES[ext]['regex'],
                          SUPPORTED_FILES[ext]['format'], ci)


def blacklisted(root, path, _cache={}):
    orig_path = path
    if path not in _cache:
        _cache[orig_path] = False
        while (path + os.path.sep).startswith(root):
            if os.path.exists(os.path.join(path, '.no-headers')):
                _cache[orig_path] = True
                break
            path = os.path.normpath(os.path.join(path, '..'))
    return _cache[orig_path]


@click.command(help=USAGE)
@click.option('--ci', is_flag=True, help='Indicate that the script is running during CI and should use a non-zero '
                                         'exit code unless all headers were already up to date. This also prevents '
                                         'files from actually being updated.')
@click.option('--year', '-y', type=click.IntRange(min=1000), default=date.today().year, metavar='YEAR',
              help='Indicate the target year')
@click.option('--path', '-p', type=click.Path(exists=True), help='Restrict updates to a specific file or directory')
@click.pass_context
def main(ctx, ci, year, path):
    error = False
    if path and os.path.isdir(path):
        if not ci:
            print(cformat('Updating headers to the year %{yellow!}{year}%{reset} for all the files in '
                          '%{yellow!}{path}%{reset}...').format(year=year, path=path))
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if not blacklisted(path, root):
                    if update_header(os.path.join(root, filename), year, ci):
                        error = True
    elif path and os.path.isfile(path):
        if not ci:
            print(cformat('Updating headers to the year %{yellow!}{year}%{reset} for the file '
                          '%{yellow!}{file}%{reset}...').format(year=year, file=path))
        if update_header(path, year, ci):
            error = True
    else:
        if not ci:
            print(cformat('Updating headers to the year %{yellow!}{year}%{reset} for all '
                          'git-tracked files...').format(year=year))
        try:
            for filepath in subprocess.check_output(['git', 'ls-files'], text=True).splitlines():
                filepath = os.path.abspath(filepath)
                if not blacklisted(os.getcwd(), os.path.dirname(filepath)):
                    if update_header(filepath, year, ci):
                        error = True
        except subprocess.CalledProcessError:
            raise click.UsageError(cformat('%{red!}You must be within a git repository to run this script.'))

    if not error:
        print(cformat('%{green}\u2705 All headers are up to date'))
    elif ci:
        print(cformat('%{red}\u274C Some headers need to be updated or added'))
        sys.exit(1)
    else:
        print(cformat('%{yellow}\U0001F504 Some headers have been updated (or are missing)'))


if __name__ == '__main__':
    main()
