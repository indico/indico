# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import ipaddress
import socket
from urllib.parse import urlsplit


def is_private_url(url):
    """Check if the provided URL points to a private IP address."""
    hostname = urlsplit(url).hostname.strip('[]')
    if '.' not in hostname and ':' not in hostname:
        return True

    try:
        host_data = socket.getaddrinfo(hostname, None, 0, 0, socket.IPPROTO_TCP)
        return any(ipaddress.ip_address(str(item[4][0])).is_private for item in host_data)
    except (socket.gaierror, ipaddress.AddressValueError, ValueError):
        return True
