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

import logging
import errno
import urlparse
import os
import signal
import socket
import sys

import werkzeug.serving
from flask import current_app
from flask_script import Command, Option
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.debug import DebuggedApplication
from werkzeug.exceptions import NotFound
from werkzeug.serving import WSGIRequestHandler
from werkzeug.wsgi import DispatcherMiddleware, SharedDataMiddleware

from indico.core.config import Config
from indico.core.logger import Logger
from indico.util import console


try:
    from OpenSSL import SSL
except ImportError:
    SSL = None


class IndicoDevServer(Command):
    """Runs the Flask development server"""

    def get_options(self):
        return (
            Option('--logging', action='store',
                   help='display logging messages for specified level'),
            Option('--host',
                   help='use a different host than the one in indico.conf'),
            Option('--port', type=int,
                   help='use a different port than the one in indico.conf'),
            Option('--keep-base-url', action='store_true',
                   help='do not update the base url with the given host/port'),
            Option('--with-ssl', action='store_true',
                   help='enable ssl support for web server'),
            Option('--ssl-key', help='path to the ssl private key file'),
            Option('--ssl-cert', help='path to the ssl certificate file'),
            Option('--disable-reloader', action='store_true',
                   help='restart the server whenever a file changes (does not work for legacy code)'),
            Option('--enable-evalex', action='store_true',
                   help="enable the werkzeug debugger's python shell in tracebacks and via /console)"),
            Option('--evalex-from', action='append', metavar='IP',
                   help="restricts the evalex shell to the given ips (can be used multiple times)"),
            Option('--quiet', action='store_true',
                   help="don't log successful requests for common static files")
        )

    def run(self, **args):
        if args['logging']:
            setup_logging(args['logging'])

        app = current_app._get_current_object()
        start_web_server(app, host=args['host'], port=args['port'], keep_base_url=args['keep_base_url'],
                         with_ssl=args['with_ssl'], ssl_cert=args['ssl_cert'], ssl_key=args['ssl_key'],
                         enable_evalex=args['enable_evalex'], evalex_from=args['evalex_from'],
                         reload_on_change=not args['disable_reloader'], quiet=args['quiet'])


def make_indico_dispatcher(wsgi_app):
    config = Config.getInstance()
    baseURL = config.getBaseURL()
    path = urlparse.urlparse(baseURL)[2].rstrip('/')
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
        elif self._evalex_whitelist is True:  # explicitly check against True!
            return True
        else:
            return self._request_ip in self._evalex_whitelist

    @evalex.setter
    def evalex(self, value):
        self._evalex_whitelist = value

    def __call__(self, environ, start_response):
        self._request_ip = environ['REMOTE_ADDR']
        return super(DebuggedIndico, self).__call__(environ, start_response)


class QuietWSGIRequestHandler(WSGIRequestHandler):
    INDICO_URL_PREFIX = ''  # set from outside based on BaseURL
    IGNORED_PATH_PREFIXES = {'/vars.js', '/js/', '/css/', '/static/', '/images/'}

    def log_request(self, code='-', size='-'):
        if code not in (304, 200):
            super(QuietWSGIRequestHandler, self).log_request(code, size)
        elif '?__debugger__=yes&cmd=resource' in self.path:
            pass  # don't log debugger resources, they are quite uninteresting
        elif not any(self.path.startswith(self.INDICO_URL_PREFIX + x) for x in self.IGNORED_PATH_PREFIXES):
            super(QuietWSGIRequestHandler, self).log_request(code, size)


class WerkzeugServer(object):
    def __init__(self, app, host='localhost', port=8000, enable_ssl=False, ssl_key=None, ssl_cert=None,
                 reload_on_change=False, use_debugger=True, evalex_whitelist=None, quiet=False):
        """
        Run an Indico server based on the Werkzeug server
        """

        if not SSL and enable_ssl:
            console.error('You need pyopenssl to use SSL')
            sys.exit(1)

        self.app = app
        self.host = host
        self.port = port
        self.ssl = enable_ssl
        self.ssl_key = ssl_key
        self.ssl_cert = ssl_cert
        self.reload_on_change = reload_on_change
        self.use_debugger = use_debugger
        self.evalex_whitelist = evalex_whitelist
        self.quiet = quiet

        logger = logging.getLogger('werkzeug')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler(sys.stderr))

        self._setup_ssl()
        self._server = None

    def _setup_ssl(self):
        if not self.ssl:
            self.ssl_context = None
        elif not self.ssl_cert and not self.ssl_key:
            self.ssl_context = 'adhoc'
        else:
            self.ssl_context = (self.ssl_cert, self.ssl_key)

    def make_server(self):
        assert self._server is None
        app = self.app
        if self.use_debugger:
            app = DebuggedIndico(app, self.evalex_whitelist)
            if Config.getInstance().getUseProxy():
                # this applies ProxyFix a second time (it's also done in configure_app),
                # but the debugger MUST receive the proper ip address or evalex ip restrictions
                # might not work as expected
                app = ProxyFix(app)
        self._server = werkzeug.serving.make_server(self.host, self.port, app, threaded=True,
                                                    request_handler=QuietWSGIRequestHandler if self.quiet else None,
                                                    ssl_context=self.ssl_context)
        self.addr = self._server.socket.getsockname()[:2]
        return self._server

    def _test_socket(self):
        # Create and destroy a socket so that any exceptions are raised before
        # we spawn a separate Python interpreter and lose this ability.
        # (taken from werkzeug.serving.run_simple)
        address_family = werkzeug.serving.select_ip_version(self.host, self.port)
        test_socket = socket.socket(address_family, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.bind((self.host, self.port))
        test_socket.close()

    def _run_new_server(self):
        # The werkzeug reloader needs a callable which creates and starts a new server
        self.make_server().serve_forever()

    def _display_host(self):
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            display_hostname = self.host != '*' and self.host or 'localhost'
            if ':' in display_hostname:
                display_hostname = '[%s]' % display_hostname
            proto = 'https' if self.ssl_context else 'http'
            console.info(' * Running on {0}://{1}:{2}'.format(proto, display_hostname, self.port))
            if self.evalex_whitelist:
                console.info(' * Werkzeug debugger console on {0}://{1}:{2}/console'.format(proto, display_hostname,
                                                                                            self.port))
                if self.evalex_whitelist is True:  # explicitly check against True!
                    console.warning(' * Werkzeug debugger console is available to all clients')

    def run(self):
        self._display_host()
        if not self.reload_on_change:
            if self._server is None:
                self.make_server()
            self._server.serve_forever()
        else:
            assert self._server is None  # otherwise the socket is already bound
            self._test_socket()
            cfg_dir = Config.getInstance().getConfigurationDir()
            extra_files = [os.path.join(cfg_dir, name) for name in ('logging.conf', 'indico.conf')]
            werkzeug.serving.run_with_reloader(self._run_new_server, extra_files)


def _can_bind_port(port):
    s = socket.socket()
    try:
        s.bind(('', port))
    except socket.error, e:
        if e.errno == errno.EACCES:
            return False
    s.close()
    return True


def _sigint(sig, frame):
    print
    # Sometimes a request hangs and prevents the interpreter from exiting.
    # By setting an 1-second alarm we avoid this
    if hasattr(signal, 'alarm'):
        signal.alarm(1)
    sys.exit(0)


def setup_logging(level):
    formatter = logging.Formatter('%(asctime)s %(name)-16s: %(levelname)-8s - %(message)s')
    logger = Logger.get()
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, level))
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def start_web_server(app, host='localhost', port=0, with_ssl=False, keep_base_url=True, ssl_cert=None, ssl_key=None,
                     reload_on_change=False, enable_evalex=False, evalex_from=None, quiet=False):
    config = Config.getInstance()
    # Let Indico know that we are using the embedded server. This causes it to re-raise exceptions so they
    # end up in the Werkzeug debugger.
    config._configVars['EmbeddedWebserver'] = True
    # We obviously do not have X-Sendfile or X-Accel-Redirect support in the embedded server
    config._configVars['StaticFileMethod'] = None

    # Get appropriate base url and defaults
    base_url = config.getBaseSecureURL() if with_ssl else config.getBaseURL()
    if not base_url:
        base_url = config.getBaseURL() or 'http://localhost'
        if with_ssl:
            port = 443
        console.warning(' * You should set {0}; retrieving host information from {1}'.format(
            'BaseSecureURL' if with_ssl else 'BaseURL',
            base_url)
        )
    default_port = 443 if with_ssl else 80
    url_data = urlparse.urlparse(base_url)

    # commandline data has priority, fallback to data from base url (or default in case of port)
    host = host or url_data.netloc.partition(':')[0]
    requested_port = used_port = port or url_data.port or default_port

    # Don't let people bind on a port they cannot use.
    if used_port < 1024 and not _can_bind_port(used_port):
        used_port += 8000
        console.warning(' * You cannot open a socket on port {}, using {} instead.'.format(requested_port, used_port))

    # By default we update the base URL with the actual host/port. The user has the option to
    # disable this though in case he wants different values, e.g. to use iptables to make his
    # development server available via port 443 while listening on a non-privileged port:
    # iptables -t nat -A PREROUTING -d YOURIP/32 -p tcp -m tcp --dport 443 -j REDIRECT --to-port 8443
    if not keep_base_url:
        scheme = 'https' if with_ssl else 'http'
        netloc = host
        if used_port != default_port:
            netloc += ':%d' % used_port
        base_url = '{0}://{1}{2}'.format(scheme, netloc, url_data.path)
    # However, if we had to change the port to avoid a permission issue we always rewrite BaseURL.
    # In this case it is somewhat safe to assume that the user is not actually trying to use the iptables hack
    # mentioned above but simply did not consider using a non-privileged port.
    elif requested_port != used_port:
        netloc = '{0}:{1}'.format(url_data.netloc.partition(':')[0], used_port)
        base_url = '{0}://{1}{2}'.format(url_data.scheme, netloc, url_data.path)

    # We update both BaseURL and BaseSecureURL to something that actually works.
    # In case of SSL-only we need both URLs to be set to the same SSL url to prevent some stuff being "loaded"
    # from an URL that is not available.
    # In case of not using SSL we clear the BaseSecureURL so the user does not need to update the config during
    # development if he needs to disable SSL for some reason.
    if with_ssl:
        config._configVars['BaseURL'] = base_url
        config._configVars['BaseSecureURL'] = base_url
    else:
        config._configVars['BaseURL'] = base_url
        config._configVars['BaseSecureURL'] = ''
    config._deriveOptions()

    if not enable_evalex:
        evalex_whitelist = False
    elif evalex_from:
        evalex_whitelist = evalex_from
    else:
        evalex_whitelist = True

    console.info(' * Using BaseURL {0}'.format(base_url))
    app.wsgi_app = make_indico_dispatcher(app.wsgi_app)
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/htmlcov': os.path.join(app.root_path, '..', 'htmlcov')
    }, cache=False)
    QuietWSGIRequestHandler.INDICO_URL_PREFIX = url_data.path.rstrip('/')
    server = WerkzeugServer(app, host, used_port, reload_on_change=reload_on_change, evalex_whitelist=evalex_whitelist,
                            enable_ssl=with_ssl, ssl_cert=ssl_cert, ssl_key=ssl_key, quiet=quiet)
    signal.signal(signal.SIGINT, _sigint)
    server.run()
