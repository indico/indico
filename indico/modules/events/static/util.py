# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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


def url_to_static_filename(url):
    # get rid of /event/1234
    url = _event_url_prefix_re.sub('', url)
    # get rid of any other leading/trailing slash and replace slashes inside
    url = url.strip('/').replace('/', '--')
    # it's not executed in a webserver, so we do need a .html extension
    return url + '.html'
