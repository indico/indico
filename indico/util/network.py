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

import ipaddress
import socket

from werkzeug.urls import url_parse


def is_private_url(url):
    """Check if the provided URL points to a private IP address."""
    hostname = url_parse(url).host.strip('[]')
    if '.' not in hostname and ':' not in hostname:
        return True

    try:
        host_data = socket.getaddrinfo(hostname, None, 0, 0, socket.IPPROTO_TCP)
        return any(ipaddress.ip_address(unicode(item[4][0])).is_private for item in host_data)
    except (socket.gaierror, ipaddress.AddressValueError):
        return True
