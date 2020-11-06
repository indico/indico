# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
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

from indico.util.console import cformat


click.disable_unicode_literals_warning = True


HEADERS = {
    'indico': """
 {comment_start} This file is part of Indico.
{comment_middle} Copyright (C) 2002 - {end_year} CERN
{comment_middle}
{comment_middle} Indico is free software; you can redistribute it and/or
{comment_middle} modify it under the terms of the MIT License; see the
{comment_middle} LICENSE file for more details.
{comment_end}
""",
    'plugins': """
 {comment_start} This file is part of the Indico plugins.
{comment_middle} Copyright (C) 2002 - {end_year} CERN
{comment_middle}
{comment_middle} The Indico plugins are free software; you can redistribute
{comment_middle} them and/or modify them under the terms of the MIT License;
{comment_middle} see the LICENSE file for more details.
{comment_end}
""",
    'plugins-cern': """
 {comment_start} This file is part of the CERN Indico plugins.
{comment_middle} Copyright (C) 2014 - {end_year} CERN
{comment_middle}
{comment_middle} The CERN Indico plugins are free software; you can redistribute
{comment_middle} them and/or modify them under the terms of the MIT License; see
{comment_middle} the LICENSE file for more details.
{comment_end}
""",
}


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


USAGE = """
Updates all the headers in the supported files ({supported_files}).
By default, all the files tracked by git in the current repository are updated
to the current year.

You need to specify which project it is (one of {projects}) to the correct
headers are used.

You can specify a year to update to as well as a file or directory.
This will update all the supported files in the scope including those not tracked
by git. If the directory does not contain any supported files (or if the file
specified is not supported) nothing will be updated.
""".format(supported_files=', '.join(SUPPORTED_FILES), projects=', '.join(HEADERS)).strip()


def gen_header(project, data, end_year):
    data['end_year'] = end_year
    return '\n'.join(line.rstrip() for line in HEADERS[project].format(**data).strip().splitlines())


def _update_header(project, file_path, year, substring, regex, data, ci):
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
                content = content[:match.start()] + gen_header(project, data, year) + content[match.end():]
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


def update_header(project, file_path, year, ci):
    ext = file_path.rsplit('.', 1)[-1]
    if ext not in SUPPORTED_FILES or not os.path.isfile(file_path):
        return False
    if os.path.basename(file_path)[0] == '.':
        return False
    return _update_header(project, file_path, year, SUBSTRING, SUPPORTED_FILES[ext]['regex'],
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
@click.argument('project')
@click.pass_context
def main(ctx, ci, project, year, path):
    if project not in HEADERS:
        click.echo(ctx.get_help())
        sys.exit(1)

    error = False
    if path and os.path.isdir(path):
        if not ci:
            print(cformat("Updating headers to the year %{yellow!}{year}%{reset} for all the files in "
                          "%{yellow!}{path}%{reset}...").format(year=year, path=path))
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if not blacklisted(path, root):
                    if update_header(project, os.path.join(root, filename), year, ci):
                        error = True
    elif path and os.path.isfile(path):
        if not ci:
            print(cformat("Updating headers to the year %{yellow!}{year}%{reset} for the file "
                          "%{yellow!}{file}%{reset}...").format(year=year, file=path))
        if update_header(project, path, year, ci):
            error = True
    else:
        if not ci:
            print(cformat("Updating headers to the year %{yellow!}{year}%{reset} for all "
                          "git-tracked files...").format(year=year))
        try:
            for filepath in subprocess.check_output(['git', 'ls-files'], text=True).splitlines():
                filepath = os.path.abspath(filepath)
                if not blacklisted(os.getcwd(), os.path.dirname(filepath)):
                    if update_header(project, filepath, year, ci):
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
