# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import os

from flask.cli import DispatchingApp
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.debug import DebuggedApplication
from werkzeug.exceptions import NotFound
from werkzeug.serving import WSGIRequestHandler, run_simple
from werkzeug.urls import url_parse
from werkzeug.wsgi import DispatcherMiddleware


def run_cmd(info, host, port, url, ssl, ssl_key, ssl_cert, quiet, proxy, enable_evalex, evalex_from):
    if port is None:
        port = 8443 if ssl else 8000

    if not enable_evalex:
        evalex_whitelist = False
    elif evalex_from:
        evalex_whitelist = evalex_from
    else:
        evalex_whitelist = True

    if not ssl:
        ssl_ctx = None
    elif ssl_key and ssl_cert:
        ssl_ctx = (ssl_cert, ssl_key)
    else:
        ssl_ctx = 'adhoc'

    if not url:
        proto = 'https' if ssl else 'http'
        url_host = '[{}]'.format(host) if ':' in host else host
        if (port == 80 and not ssl) or (port == 443 and ssl):
            url = '{}://{}'.format(proto, url_host)
        else:
            url = '{}://{}:{}'.format(proto, url_host, port)

    os.environ.pop('FLASK_DEBUG', None)
    os.environ['INDICO_CONF_OVERRIDE'] = repr({
        'EmbeddedWebserver': True,
        'BaseURL': url,
    })

    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print ' * Serving Indico on {}'.format(url)
        if evalex_whitelist:
            print ' * Werkzeug debugger console on {}/console'.format(url)
            if evalex_whitelist is True:  # noqa
                print ' * Werkzeug debugger console is available to all clients!'

    try:
        from indico.core.config import get_config_path
        extra_files = [get_config_path()]
    except Exception:
        extra_files = None

    # our own logger initialization code runs earlier so werkzeug
    # doesn't initialize its logger
    import logging
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.addHandler(logging.StreamHandler())

    app = _make_wsgi_app(info, url, evalex_whitelist, proxy)
    run_simple(host, port, app,
               use_reloader=True, use_debugger=False, use_evalex=False, threaded=True, ssl_context=ssl_ctx,
               extra_files=extra_files, request_handler=QuietWSGIRequestHandler if quiet else None)


def _reset_state():
    # XXX: This hack is extremely awful, but when the reloader encounters
    # an error during import / app creation time (e.g. saving a file with
    # a syntax error) and the error is fixed later we still have the old
    # data which then breaks things, so we clear them if possible (and not
    # care about any exceptions while trying to import these things)
    # The reason for this behavior is that a file that fails to import
    # is not added to `sys.modules` so the reloader won't monitor it for
    # changes.
    from indico.core.config import Config
    from indico.core.celery import celery
    Config._Config__instance = None
    celery.flask_app = None


def _make_wsgi_app(info, url, evalex_whitelist, proxy):
    def _load_app():
        _reset_state()
        return info.load_app()

    url_data = url_parse(url)
    app = DispatchingApp(_load_app)
    app = DebuggedIndico(app, evalex_whitelist)
    app = _make_indico_dispatcher(app, url_data.path)
    if proxy:
        app = ProxyFix(app)
    QuietWSGIRequestHandler.INDICO_URL_PREFIX = url_data.path.rstrip('/')
    return app


def _make_indico_dispatcher(wsgi_app, path):
    path = path.rstrip('/')
    if not path:
        # Nothing to dispatch
        return wsgi_app
    else:
        return DispatcherMiddleware(NotFound(), {
            path: wsgi_app
        })


class DebuggedIndico(DebuggedApplication):
    def __init__(self, *args, **kwargs):
        self._evalex_whitelist = None
        self._request_ip = None
        super(DebuggedIndico, self).__init__(*args, **kwargs)

    @property
    def evalex(self):
        if not self._evalex_whitelist:
            return False
        elif self._evalex_whitelist is True:  # noqa
            return True
        else:
            return self._request_ip in self._evalex_whitelist

    @evalex.setter
    def evalex(self, value):
        self._evalex_whitelist = value

    def __call__(self, environ, start_response):
        self._request_ip = environ['REMOTE_ADDR']
        if self._request_ip.startswith('::ffff:'):
            # convert ipv6-style ipv4 to the regular ipv4 notation
            self._request_ip = self._request_ip[7:]
        return super(DebuggedIndico, self).__call__(environ, start_response)


class QuietWSGIRequestHandler(WSGIRequestHandler):
    INDICO_URL_PREFIX = ''  # set from outside based on the url path prefix
    IGNORED_PATH_PREFIXES = {'/vars.js', '/js/', '/css/', '/static/', '/images/', '/assets/'}

    def log_request(self, code='-', size='-'):
        if code not in (304, 200):
            super(QuietWSGIRequestHandler, self).log_request(code, size)
        elif '?__debugger__=yes&cmd=resource' in self.path:
            pass  # don't log debugger resources, they are quite uninteresting
        elif not any(self.path.startswith(self.INDICO_URL_PREFIX + x) for x in self.IGNORED_PATH_PREFIXES):
            super(QuietWSGIRequestHandler, self).log_request(code, size)
