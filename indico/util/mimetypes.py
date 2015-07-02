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

from __future__ import unicode_literals

import re


def icon_from_mimetype(mimetype, default_icon='icon-file-filled'):
    exact_mapping = {
        'application/json': 'icon-file-css',
        'text/css': 'icon-file-css',
        'text/calendar': 'icon-calendar',
        # Word
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'icon-file-word',
        'application/msword': 'icon-file-word',
        # PDF
        'application/pdf': 'icon-file-pdf',
        # Excel
        'application/vnd.ms-excel': 'icon-file-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'icon-file-excel',
        # Powerpoint
        'application/vnd.ms-powerpoint': 'icon-file-presentation',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'icon-file-presentation',
        # Archive
        'application/x-7z-compressed': 'icon-file-zip',
        'application/x-ace-compressed': 'icon-file-zip',
        'application/x-rar-compressed': 'icon-file-zip',
        'application/x-tar': 'icon-file-zip',
        'application/zip': 'icon-file-zip',
        # Markup Languages
        'application/xml': 'icon-file-xml',
        'text/xml': 'icon-file-xml',
        'text/n3': 'icon-file-xml',
        'text/html': 'icon-file-xml',
        'text/sgml': 'icon-file-xml',
        # X-separated-values
        'text/csv': 'icon-file-spreadsheet',
        'text/tab-separated-values': 'icon-file-spreadsheet',
    }
    regex_mapping = [
        # Archive
        ('^application/x-bzip', 'icon-file-zip'),  # matches Bzip and Bzip2
        # Audio
        ('^audio/', 'icon-file-music'),
        # Images
        ('^image/', 'icon-file-image'),
        # Text
        ('^text/', 'icon-file-text'),
        # Video
        ('^video/', 'icon-file-video'),
        # OpenOffice
        ('application/vnd\.oasis\.opendocument\.', 'icon-file-openoffice'),
        # XML
        ('.+/.+\+xml$', 'icon-file-xml'),
        # JSON
        ('.+/.+\+json$', 'icon-file-css)')
    ]
    for type_, icon in exact_mapping.iteritems():
        if type_ == mimetype:
            return icon
    for pattern, icon in regex_mapping:
        if re.search(pattern, mimetype):
            return icon
    return default_icon
