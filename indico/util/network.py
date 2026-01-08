# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import ipaddress
import socket
from urllib.parse import urlsplit

from requests import Response
from requests.exceptions import RequestException


def _is_private_ip(ip):
    ip_data = ipaddress.ip_address(ip)
    return ip_data.is_private or ip_data.is_loopback or ip_data.is_reserved or ip_data.is_link_local


def is_private_url(url):
    """Check if the provided URL points to a private IP address."""
    hostname = urlsplit(url).hostname
    if not hostname:
        # invalid url, just consider it private to avoid failing noisly...
        return True
    hostname = hostname.strip('[]')
    if '.' not in hostname and ':' not in hostname:
        return True

    try:
        host_data = socket.getaddrinfo(hostname, None, 0, 0, socket.IPPROTO_TCP)
        return any(_is_private_ip(str(item[4][0])) for item in host_data)
    except (socket.gaierror, ipaddress.AddressValueError, ValueError):
        return True


class InsecureRequestError(RequestException):
    pass


def validate_request_url(url: str):
    """Check that a user-provided URL is safe to be requested.

    This should be used before making outgoing requests to user-controlled URLs to
    avoid SSRF issues. When redirects are followed (the default behavior of `requests`
    unless ``allow_redirects=False`` is used), you MUST also enable the corresponding
    hook using ``hooks={'response': validate_redirect_target_hook}`` or
    ``**make_validate_request_url_hook()`` when making the request.
    """
    # This could also allow for configurable whitelisting of specific hosts, but until
    # someone needs this let's keep it simple and just blacklist private ranges.
    if is_private_url(url):
        raise InsecureRequestError('Cannot make request to disallowed URL')


def validate_redirect_target_hook(resp: Response, *args, **kwargs) -> None:
    """Validate the redirect target of an HTTP response.

    This checks that a redirect response does not redirect to a disallowed URL.
    """
    if not resp.is_redirect:
        return
    target = resp.headers.get('location')
    try:
        validate_request_url(target)
    except InsecureRequestError as exc:
        raise InsecureRequestError('Request redirected to disallowed URL') from exc


def make_validate_request_url_hook():
    """Util to get the requests hook in a more concise way.

    Use it like this: ``requests.get(..., **make_validate_request_url_hook())``
    """
    return {'hooks': {'response': validate_redirect_target_hook}}
