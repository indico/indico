# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import print_function, unicode_literals

import os
import re
import subprocess
import sys
from datetime import date

from indico.util.console import cformat


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
        'regex': re.compile(br'((^#|[\r\n]#).*)*'),
        'format': {'comment_start': b'#', 'comment_middle': b'#', 'comment_end': b''}},
    'wsgi': {
        'regex': re.compile(br'((^#|[\r\n]#).*)*'),
        'format': {'comment_start': b'#', 'comment_middle': b'#', 'comment_end': b''}},
    'js': {
        'regex': re.compile(br'/\*(.|[\r\n])*?\*/|((^//|[\r\n]//).*)*'),
        'format': {'comment_start': b'//', 'comment_middle': b'//', 'comment_end': b''}},
    'jsx': {
        'regex': re.compile(br'/\*(.|[\r\n])*?\*/|((^//|[\r\n]//).*)*'),
        'format': {'comment_start': b'//', 'comment_middle': b'//', 'comment_end': b''}},
    'css': {
        'regex': re.compile(br'/\*(.|[\r\n])*?\*/'),
        'format': {'comment_start': b'/*', 'comment_middle': b' *', 'comment_end': b' */'}},
    'scss': {
        'regex': re.compile(br'/\*(.|[\r\n])*?\*/|((^//|[\r\n]//).*)*'),
        'format': {'comment_start': b'//', 'comment_middle': b'//', 'comment_end': b''}},
}


# The substring which must be part of a comment block in order for the comment to be updated by the header.
SUBSTRING = b'This file is part of'


USAGE = """
python bin/maintenance/update_header.py <PROJECT> [YEAR] [PATH]

Updates all the headers in the supported files ({supported_files}).
By default, all the files tracked by git in the current repository are updated
to the current year.

You need to specify which project it is (one of {projects}) to the correct
headers are used.

You can specify a year (1000-2999) to update to as well as a file or directory.
This will update all the supported files in the scope including those not tracked
by git. If the directory does not contain any supported files (or if the file
specified is not supported) nothing will be updated.
""".format(supported_files=', '.join(SUPPORTED_FILES), projects=', '.join(HEADERS)).strip()


def gen_header(project, data, end_year):
    data['end_year'] = end_year
    return '\n'.join(line.rstrip() for line in HEADERS[project].format(**data).strip().splitlines()).encode('ascii')


def _update_header(project, file_path, year, substring, regex, data):
    found = False
    with open(file_path, 'rb') as file_read:
        content = orig_content = file_read.read()
        if not content.strip():
            return
        shebang_line = None
        if content.startswith(b'#!/'):
            shebang_line, content = content.split('\n', 1)
        for match in regex.finditer(content):
            if substring in match.group():
                found = True
                content = content[:match.start()] + gen_header(project, data, year) + content[match.end():]
        if shebang_line:
            content = shebang_line + '\n' + content
    if content != orig_content:
        print(cformat('%{green!}Updating header of %{blue!}{}').format(os.path.relpath(file_path)))
        with open(file_path, 'wb') as file_write:
            file_write.write(content)
    elif not found:
        print(cformat('%{yellow}Missing header in %{yellow!}{}').format(os.path.relpath(file_path)))
        return True


def update_header(project, file_path, year):
    ext = file_path.rsplit('.', 1)[-1]
    if ext not in SUPPORTED_FILES or not os.path.isfile(file_path):
        return
    if os.path.basename(file_path)[0] == '.':
        return
    return _update_header(project, file_path, year, SUBSTRING, SUPPORTED_FILES[ext]['regex'],
                          SUPPORTED_FILES[ext]['format'])


def _process_args(args):
    year_regex = re.compile('^[12][0-9]{3}$')  # Year range 1000 - 2999
    year = date.today().year

    project = args[0]
    args = args[1:]
    if project not in HEADERS:
        print(USAGE)
        sys.exit(1)

    # Take year argument if we have one
    if args and year_regex.match(args[0]):
        year = int(args[0])
        args = args[1:]
    if not args:
        return project, year, None, None
    elif os.path.isdir(args[0]):
        return project, year, args[0], None
    elif os.path.isfile(args[0]):
        return project, year, None, args[0]
    else:
        print(USAGE)
        sys.exit(1)


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


def main():
    if '-h' in sys.argv[1:] or '--help' in sys.argv[1:] or not sys.argv[1:]:
        print(USAGE)
        sys.exit(1)

    project, year, path, file_ = _process_args(sys.argv[1:])
    error = False

    if path is not None:
        print(cformat("Updating headers to the year %{yellow!}{year}%{reset} for all the files in "
                      "%{yellow!}{path}%{reset}...").format(year=year, path=path))
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if not blacklisted(path, root):
                    error = update_header(project, os.path.join(root, filename), year) or error
    elif file_ is not None:
        print(cformat("Updating headers to the year %{yellow!}{year}%{reset} for the file "
                      "%{yellow!}{file}%{reset}...").format(year=year, file=file_))
        error = update_header(project, file_, year) or error
    else:
        print(cformat("Updating headers to the year %{yellow!}{year}%{reset} for all "
                      "git-tracked files...").format(year=year))
        try:
            for path in subprocess.check_output(['git', 'ls-files']).splitlines():
                path = os.path.abspath(path)
                if not blacklisted(os.getcwd(), os.path.dirname(path)):
                    error = update_header(project, path, year) or error
        except subprocess.CalledProcessError:
            print(cformat('%{red!}[ERROR] you must be within a git repository to run this script.'), file=sys.stderr)
            print(USAGE)
            sys.exit(1)

    if error:
        sys.exit(1)


if __name__ == '__main__':
    main()
