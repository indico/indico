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

import base64
import mimetypes
import re
import urlparse
from contextlib import contextmanager

import requests
from flask import current_app, g, request
from flask_webpackext import current_webpack
from flask_webpackext.manifest import JinjaManifestEntry
from pywebpack import Manifest
from werkzeug.urls import url_parse

from indico.core.config import config
from indico.modules.events.layout.models.images import ImageFile
from indico.web.flask.util import find_url_endpoint


_css_url_re = re.compile(r"url\('?([^\)']+)'?\)", re.MULTILINE)
_event_url_prefix_re = re.compile(r'^/event/\d+')
_url_has_extension_re = re.compile(r'.*\.([^/]+)$')
_static_url_pattern = r'({})?/(images|dist|fonts)(.*)/(.+?)(__v[0-9a-f]+)?\.([^.]+)$'
_custom_url_pattern = r'(?:{})?/static/custom/(.+)$'


def rewrite_static_url(path):
    """Remove __vxxx prefix from static URLs."""
    static_pattern = _static_url_pattern.format(url_parse(config.BASE_URL).path)
    custom_pattern = _custom_url_pattern.format(url_parse(config.BASE_URL).path)
    if re.match(static_pattern, path):
        return re.sub(static_pattern, r'static/\2\3/\4.\6', path)
    else:
        return re.sub(custom_pattern, r'static/custom/\1', path)


def _create_data_uri(url, filename):
    """Create a data url that contains the file in question."""
    response = requests.get(url, verify=False)
    if response.status_code != 200:
        # couldn't access the file
        return url
    data = base64.b64encode(response.content)
    content_type = (mimetypes.guess_type(filename)[0] or
                    response.headers.get('Content-Type', 'application/octet-stream'))
    return 'data:{};base64,{}'.format(content_type, data)


def _rewrite_event_asset_url(event, url):
    """Rewrite URLs of assets such as event images.

    Only assets contained within the event will be taken into account
    """
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(url)

    netloc = netloc or current_app.config['SERVER_NAME']
    scheme = scheme or 'https'

    # internal URLs (same server)
    if netloc == current_app.config['SERVER_NAME']:
        # this piece of Flask magic finds the endpoint that corresponds to
        # the URL and checks that it points to an image belonging to this event
        endpoint, data = find_url_endpoint(path)
        if (endpoint == 'event_images.image_display' and data['confId'] == event.id
                and ImageFile.get(data['image_id']).event == event):
            return 'images/{image_id}-{filename}'.format(**data)
    # if the URL is not internal or just not an image,
    # we embed the contents using a data URI
    return _create_data_uri(urlparse.urlunsplit((scheme, netloc, path, qs, '')), urlparse.urlsplit(path)[-1])


def _remove_anchor(url):
    """Remove the anchor from a URL."""
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(url)
    return urlparse.urlunsplit((scheme, netloc, path, qs, ''))


def rewrite_css_urls(event, css):
    """Rewrite CSS in order to handle url(...) properly."""
    # keeping track of used URLs
    used_urls = set()

    def _replace_url(m):
        url = m.group(1)
        if url.startswith('/event/') or re.match('https?:', url):
            rewritten_url = _rewrite_event_asset_url(event, url)
            return 'url({})'.format(rewritten_url)
        else:
            rewritten_url = rewrite_static_url(url)
            used_urls.add(_remove_anchor(rewritten_url))
            return "url('../../../{}')".format(rewritten_url)
    return _css_url_re.sub(_replace_url, css), used_urls


def url_to_static_filename(endpoint, url):
    """Handle special endpoint/URLs so that they link to offline content."""
    if re.match('(events)?\.display(_overview)?$', endpoint):
        return 'index.html'
    elif endpoint == 'event_layout.css_display':
        return 'custom.css'

    # get rid of /event/1234
    url = _event_url_prefix_re.sub('', url)
    indico_path = url_parse(config.BASE_URL).path
    if re.match(_static_url_pattern.format(indico_path), url):
        url = rewrite_static_url(url)
    else:
        url = re.sub(r'{}/(.*)'.format(indico_path), r'\1', url)
        if not url.startswith('assets/'):
            # replace all remaining slashes
            url = url.replace('/', '--')
    # it's not executed in a webserver, so we do need a .html extension
    if not _url_has_extension_re.match(url):
        url += '.html'
    return url


def _rule_for_endpoint(endpoint):
    return next((x for x in current_app.url_map.iter_rules(endpoint) if 'GET' in x.methods), None)


@contextmanager
def override_request_endpoint(endpoint):
    rule = _rule_for_endpoint(endpoint)
    assert rule is not None
    old_rule = request.url_rule
    request.url_rule = rule
    try:
        yield
    finally:
        request.url_rule = old_rule


class RewrittenManifest(Manifest):
    """A manifest that rewrites its asset paths."""

    def __init__(self, manifest):
        super(RewrittenManifest, self).__init__()
        self._entries = {k: JinjaManifestEntry(entry.name, self._rewrite_paths(entry._paths))
                         for k, entry in manifest._entries.viewitems()}
        self.used_assets = set()

    def _rewrite_paths(self, paths):
        return [rewrite_static_url(path) for path in paths]

    def __getitem__(self, key):
        self.used_assets.add(key)
        return super(RewrittenManifest, self).__getitem__(key)


@contextmanager
def collect_static_files():
    """Keep track of URLs used by manifest and url_for."""
    manifest = RewrittenManifest(current_webpack.manifest)
    g.custom_manifest = manifest
    g.used_url_for_assets = set()
    used_assets = set()
    yield used_assets
    used_assets |= {p for k in manifest.used_assets for p in manifest[k]._paths}
    used_assets |= {rewrite_static_url(url) for url in g.used_url_for_assets}
    g.pop('custom_manifest')
    g.pop('used_url_for_assets')
