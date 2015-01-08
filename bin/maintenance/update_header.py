# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import os
import re
import sys
from datetime import date
from subprocess import check_output, CalledProcessError


HEADER = """
 {comment_start} This file is part of Indico.
{comment_middle} Copyright (C) 2002 - {end_year} European Organization for Nuclear Research (CERN).
{comment_middle}
{comment_middle} Indico is free software; you can redistribute it and/or
{comment_middle} modify it under the terms of the GNU General Public License as
{comment_middle} published by the Free Software Foundation; either version 3 of the
{comment_middle} License, or (at your option) any later version.
{comment_middle}
{comment_middle} Indico is distributed in the hope that it will be useful, but
{comment_middle} WITHOUT ANY WARRANTY; without even the implied warranty of
{comment_middle} MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
{comment_middle} General Public License for more details.
{comment_middle}
{comment_middle} You should have received a copy of the GNU General Public License
{comment_middle} along with Indico; if not, see <http://www.gnu.org/licenses/>.
{comment_end}
"""


"""
Dictionary listing the files for which to change the header.

The key is the extension of the file (without the dot) and the value is another
dictionary containing two keys:
  - 'regex' : A regular expression matching comments in the given file type
  - 'format': A dictionary with the comment characters to add to the header.
              There must be a `comment_start` inserted before the header,
              `comment_middle` inserted at the beginning of each line except the
              first and last one, and `comment_end` inserted at the end of the
              header. (See the `HEADER` above)
"""
SUPPORTED_FILES = {
    'py': {
        'regex': re.compile('((^#|[\r\n]#).*)*'),
        'format': {'comment_start': '#', 'comment_middle': '#', 'comment_end': ''}},
    'wsgi': {
        'regex': re.compile('((^#|[\r\n]#).*)*'),
        'format': {'comment_start': '#', 'comment_middle': '#', 'comment_end': ''}},
    'sh': {
        'regex': re.compile('((^#|[\r\n]#).*)*'),
        'format': {'comment_start': '#', 'comment_middle': '#', 'comment_end': ''}},
    'js': {
        'regex': re.compile('/\*(.|[\r\n])*?\*/'),
        'format': {'comment_start': '/*', 'comment_middle': ' *', 'comment_end': ' */'}},
    'css': {
        'regex': re.compile('/\*(.|[\r\n])*?\*/'),
        'format': {'comment_start': '/*', 'comment_middle': ' *', 'comment_end': ' */'}},
    'scss': {
        'regex': re.compile('/\*(.|[\r\n])*?\*/'),
        'format': {'comment_start': '/*', 'comment_middle': ' *', 'comment_end': ' */'}},
    'xsl': {
        'regex': re.compile('<\!--(.|[\r\n])*?-->'),
        'format': {'comment_start': '<!--\n   ', 'comment_middle': '   ', 'comment_end': '-->'}},
}


"""
The substring which must be part of a comment block in order for the comment to
be updated by the header.
"""
SUBSTRING = 'Indico is free software;'


USAGE = """
python bin/maintenance/update_header.py [YEAR] [PATH]

Updates all the header in the supported files ({supported_files}).
By default, all the files tracked by git in the current repository are updated
to the current year.

You can specify a file or directory to update as well as a year (1000-2999) to
update to, in the order you prefer. This will update all the supported files in
the scope including those not tracked by git. IF the directory does not contain
any supported files (or if the file specified is not supported) they (it) will
not be updated.
""".format(supported_files=', '.join(SUPPORTED_FILES.iterkeys())).strip()


def gen_header(format, end_year):
    format['end_year'] = end_year
    return '\n'.join(line.rstrip() for line in HEADER.format(**format).strip().splitlines())


def _update_header(file_path, year, substring, regex, format):
    modified = False
    with open(file_path, 'r') as file_read:
        content = file_read.read()
        for match in regex.finditer(content):
            if substring in match.group():
                print('{0}[{1}-{2}]'.format(file_path, match.start(), match.end()))
                content = content[:match.start()] + gen_header(format, year) + content[match.end():]
                modified = True
        if modified:
            with open(file_path + '.tmp', 'w') as file_write:
                file_write.write(content)
    if modified:
        os.rename(file_path + '.tmp', file_path)


def update_header(file_path, year):
    ext = file_path.rsplit('.', 1)[-1]
    if ext not in SUPPORTED_FILES:
        return
    _update_header(file_path, year, SUBSTRING, SUPPORTED_FILES[ext]['regex'], SUPPORTED_FILES[ext]['format'])


def _process_args(*args):
    year_regex = re.compile('^[12][0-9]{3}$')  # Year range 1000 - 2999
    year, path, file_ = None, None, None

    try:
        if len(sys.argv) >= 4:
            error_msg = ("[ERROR] At most 2 arguments, the license's end year and\n"
                         "        a valid path (to a file or directory), are accepted.\n")
            raise ValueError

        elif len(sys.argv) == 3:  # year and path
            error_msg = ("[ERROR] The arguments must be a valid path (to a file or directory)\n"
                         "        and the license's end year, or vice-versa.\n")
            _, arg1, arg2 = sys.argv

            if year_regex.match(arg1):
                year = arg1
                if os.path.isdir(arg2):     # year directory
                    path = os.path.abspath(arg2)
                elif os.path.isfile(arg2):  # year file
                    file_ = os.path.abspath(arg2)
                else:
                    raise ValueError
            elif year_regex.match(arg2):
                year = arg2
                if os.path.isdir(arg1):     # directory year
                    path = os.path.abspath(arg1)
                elif os.path.isfile(arg1):  # file year
                    file_ = os.path.abspath(arg1)
                else:
                    raise ValueError

        elif len(sys.argv) == 2:  # year or path
            error_msg = ("[ERROR] The argument must be a valid path (to a file or directory)\n"
                         "        or the license's end year.\n")
            arg = sys.argv[1]

            if year_regex.match(arg):
                year = arg
            elif os.path.isdir(arg):
                path = os.path.abspath(arg)
            elif os.path.isfile(arg):
                file_ = os.path.abspath(arg)
            else:
                raise ValueError

        if year is None:
            year = date.today().year
    except ValueError:
        print(error_msg, file=sys.stderr)
        print(USAGE)
        sys.exit(1)

    return year, path, file_


def main():

    year, path, file_ = _process_args(*sys.argv)

    if path is not None:
        print("updating headers to the year {year} for all the files in {path}...".format(year=year, path=path))
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                update_header(os.path.join(root, filename), year)
    elif file_ is not None:
        print("updating headers to the year {year} for the file {file}...".format(year=year, file=file_))
        update_header(file_, year)
    else:
        print("updating headers to the year {year} for all git-tracked files...".format(year=year))
        try:
            for path in check_output(['git', 'ls-files']).splitlines():
                update_header(os.path.abspath(path), year)
        except CalledProcessError:
            print('[ERROR] you must be within a git repository to run this script.\n', file=sys.stderr)
            print(USAGE)
            sys.exit(1)


if __name__ == '__main__':
    main()
