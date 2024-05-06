# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import traceback
from threading import Lock, Thread
from urllib.parse import urlsplit

import click
from werkzeug.debug import DebuggedApplication
from werkzeug.exceptions import NotFound
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.serving import WSGIRequestHandler, run_simple


def run_cmd(info, **kwargs):
    if kwargs.pop('reloader_type') == 'watchfiles':
        run_watchfiles()
        return

    run_server(info, **kwargs)


def run_watchfiles():
    from .watchfiles import Watchfiles
    Watchfiles().run()


def run_server(info, host, port, url, ssl, ssl_key, ssl_cert, quiet, proxy, enable_evalex, evalex_from):
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
        url_host = f'[{host}]' if ':' in host else host
        if (port == 80 and not ssl) or (port == 443 and ssl):
            url = f'{proto}://{url_host}'
        else:
            url = f'{proto}://{url_host}:{port}'

    os.environ['INDICO_DEV_SERVER'] = '1'
    os.environ.pop('FLASK_DEBUG', None)
    os.environ['INDICO_CONF_OVERRIDE'] = repr({
        'BASE_URL': url,
    })

    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print(f' * Serving Indico on {url}')
        if evalex_whitelist:
            print(f' * Werkzeug debugger console on {url}/console')
            if evalex_whitelist is True:
                print(' * Werkzeug debugger console is available to all clients!')

    try:
        from indico.core.config import get_config_path
        extra_files = [get_config_path()]
    except Exception:
        extra_files = None

    # our own logger initialization code runs earlier so werkzeug
    # doesn't initialize its logger
    import logging
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.propagate = False
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.addHandler(logging.StreamHandler())

    app = _make_wsgi_app(info, url, evalex_whitelist, proxy)
    run_simple(host, port, app,
               reloader_type='none', use_reloader=False,
               use_debugger=False, use_evalex=False, threaded=True, ssl_context=ssl_ctx,
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
    from indico.core.celery import celery
    celery.flask_app = None


def _make_wsgi_app(info, url, evalex_whitelist, proxy):
    def _load_app():
        _reset_state()
        return info.load_app()

    url_data = urlsplit(url)
    app = DispatchingApp(_load_app)
    app = DebuggedIndico(app, evalex_whitelist)
    app.trusted_hosts = [url_data.netloc]
    app = _make_indico_dispatcher(app, url_data.path)
    if proxy:
        app = ProxyFix(app, x_for=1, x_proto=1, x_host=1)
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


# Taken from Flask - it was removed, but we want to keep the initial-lazy-loading
# behavior to ensure fast startup e.g. after a reload from a file change watcher
class DispatchingApp:
    """
    Special application that dispatches to a Flask application which
    is imported by name in a background thread.  If an error happens
    it is recorded and shown as part of the WSGI handling which in case
    of the Werkzeug debugger means that it shows up in the browser.
    """

    def __init__(self, loader):
        self.loader = loader
        self._app = None
        self._lock = Lock()
        self._bg_loading_exc = None
        self._load_in_background()

    def _load_in_background(self):
        # Store the Click context and push it in the loader thread so
        # script_info is still available.
        ctx = click.get_current_context(silent=True)

        def _load_app():
            __traceback_hide__ = True  # noqa: F841

            with self._lock:
                if ctx is not None:
                    click.globals.push_context(ctx)

                try:
                    self._load_unlocked()
                except Exception as e:
                    traceback.print_exc()
                    self._bg_loading_exc = e

        t = Thread(target=_load_app, args=())
        t.start()

    def _flush_bg_loading_exception(self):
        __traceback_hide__ = True  # noqa: F841
        exc = self._bg_loading_exc

        if exc is not None:
            self._bg_loading_exc = None
            raise exc

    def _load_unlocked(self):
        __traceback_hide__ = True  # noqa: F841
        self._app = rv = self.loader()
        self._bg_loading_exc = None
        return rv

    def __call__(self, environ, start_response):
        __traceback_hide__ = True  # noqa: F841
        if self._app is not None:
            return self._app(environ, start_response)
        self._flush_bg_loading_exception()
        with self._lock:
            if self._app is not None:
                rv = self._app
            else:
                rv = self._load_unlocked()
            return rv(environ, start_response)


class DebuggedIndico(DebuggedApplication):
    def __init__(self, *args, **kwargs):
        self._evalex_whitelist = None
        self._request_ip = None
        super().__init__(*args, **kwargs)

    @property
    def evalex(self):
        if not self._evalex_whitelist:
            return False
        elif self._evalex_whitelist is True:
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
        return super().__call__(environ, start_response)


class QuietWSGIRequestHandler(WSGIRequestHandler):
    INDICO_URL_PREFIX = ''  # set from outside based on the url path prefix
    IGNORED_PATH_PREFIXES = {'/vars.js', '/css/', '/fonts/', '/images/', '/dist/', '/assets/', '/static/'}

    def log_request(self, code='-', size='-'):
        if code not in (304, 200):
            super().log_request(code, size)
        elif '?__debugger__=yes&cmd=resource' in self.path:
            pass  # don't log debugger resources, they are quite uninteresting
        elif not any(self.path.startswith(self.INDICO_URL_PREFIX + x) for x in self.IGNORED_PATH_PREFIXES):
            super().log_request(code, size)
