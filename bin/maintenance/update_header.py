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


def gen_header(format, end_year):
    format['end_year'] = end_year
    return '\n'.join(line.rstrip() for line in HEADER.format(**format).strip().splitlines())


def _update_header(file_path, year, substring, regex, format):
    modified = False
    with open(file_path, 'r') as file_read:
        content = file_read.read()
        for match in regex.finditer(content):
            if substring in match.group():
                print '{0}[{1}-{2}]'.format(file_path, match.start(), match.end())
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


def main():
    year = sys.argv[1] if len(sys.argv) == 2 else date.today().year
    print 'updating headers to the year {year}...'.format(year=year)

    try:
        for path in check_output(['git', 'ls-files']).splitlines():
            update_header(os.path.abspath(path), year)
    except CalledProcessError:
        print '[ERROR] you must be within a git repository to run this script.'
        sys.exit(1)


if __name__ == '__main__':
    main()
