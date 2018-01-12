# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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


_event_url_prefix_re = re.compile(r'^/event/\d+')
_url_has_extension_re = re.compile(r'.*\.([^/]+)$')


def url_to_static_filename(endpoint, url):
    if endpoint.endswith('.static') or endpoint in ('event_images.logo_display', 'event_layout.css_display'):
        # these urls need to remain intact to be downloaded via a HTTP request
        return url
    # get rid of /event/1234
    url = _event_url_prefix_re.sub('', url)
    # get rid of any other leading slash
    url = url.strip('/')
    if not url.startswith('assets/'):
        # replace all remaining slashes
        url = url.replace('/', '--')
    # it's not executed in a webserver, so we do need a .html extension
    if not _url_has_extension_re.match(url):
        url += '.html'
    return url
