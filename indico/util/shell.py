# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import logging
import argparse
import errno
import urlparse
import os
import signal
import socket
import sys
import werkzeug.serving
from SocketServer import TCPServer
from werkzeug.debug import DebuggedApplication
from werkzeug.exceptions import NotFound
from werkzeug.wsgi import DispatcherMiddleware

try:
    from OpenSSL import SSL
except ImportError:
    SSL = None

from indico.web.flask.app import make_app
from indico.core.index import Catalog
from indico.util import console

## indico legacy imports
import MaKaC
from indico.core.config import Config
from indico.core.db import DBMgr
from MaKaC.conference import Conference, Category, ConferenceHolder, CategoryManager
from MaKaC.user import AvatarHolder, GroupHolder
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.indexes import IndexesHolder
from MaKaC.common.logger import Logger
from MaKaC.plugins.base import PluginsHolder
from MaKaC.webinterface.rh.JSContent import RHGetVarsJs


try:
    HAS_IPYTHON = True
    try:
        # IPython >=1.0
        from IPython.terminal.embed import InteractiveShellEmbed
    except ImportError:
        from IPython.frontend.terminal.embed import InteractiveShellEmbed
    from IPython.config.loader import Config as IPConfig
    OLD_IPYTHON = False
except ImportError:
    try:
        # IPython <0.12
        from IPython.Shell import IPShellEmbed
        OLD_IPYTHON = True
    except ImportError:
        import code
        HAS_IPYTHON = False

SHELL_BANNER = console.colored('\nindico {0}\n'.format(MaKaC.__version__), 'yellow')


def add(namespace, element, name=None, doc=None):

    if not name:
        name = element.__name__
    namespace[name] = element

    if doc:
        print console.colored('+ {0} : {1}'.format(name, doc), 'green')
    else:
        print console.colored('+ {0}'.format(name), 'green')


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


class WerkzeugServer(object):

    def __init__(self, app, host='localhost', port=8000, enable_ssl=False, ssl_key=None, ssl_cert=None,
                 reload_on_change=False, use_debugger=True):
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

        logger = logging.getLogger('werkzeug')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler(sys.stderr))

        self._setup_ssl()
        self._server = None

    def _setup_ssl(self):
        if not self.ssl:
            self.ssl_context = None
        elif not self.ssl_cert and not self.ssl_key:
            self._patch_shutdown_request()
            self.ssl_context = 'adhoc'
        else:
            self._patch_shutdown_request()
            self.ssl_context = SSL.Context(SSL.SSLv23_METHOD)
            self.ssl_context.use_privatekey_file(self.ssl_key)
            self.ssl_context.use_certificate_chain_file(self.ssl_cert)

    def make_server(self):
        assert self._server is None
        app = self.app
        if self.use_debugger:
            # In case anyone wonders why evalex is disabled:
            # 1. It's a huge security hole when open to the public. To use it properly we'd need a way to
            #    restrict it by IP address (or disable it when not listening on localhost)
            # 2. ZODB uses a thread-local field to store the connection. So anything accessing the DB will not work
            #    when accessed from the debugger shell.
            # So the best solution is not using that part of the werkzeug debugger at all.
            # Simply use e.g. pydev or rpdb2 if you want a debugger.
            app = DebuggedApplication(app, False)
        self._server = werkzeug.serving.make_server(self.host, self.port, app, threaded=True,
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
            console.info(' * Running on {0}://{1}:{2}'.format('https' if self.ssl_context else 'http',
                                                              display_hostname, self.port))

    def run(self):
        self._display_host()
        if not self.reload_on_change:
            if self._server is None:
                self.make_server()
            self._server.serve_forever()
        else:
            assert self._server is None  # otherwise the socket is already bound
            self._test_socket()
            werkzeug.serving.run_with_reloader(self._run_new_server)

    @staticmethod
    def _patch_shutdown_request():
        # Fix SocketServer's shutdown not working with pyopenssl
        def my_shutdown_request(self, request):
            """Called to shutdown and close an individual request."""
            try:
                #explicitly shutdown.  socket.close() merely releases
                #the socket and waits for GC to perform the actual close.
                try:
                    request.shutdown(socket.SHUT_WR)
                except TypeError:
                    # ssl sockets don't support an argument
                    try:
                        request.shutdown()
                    except SSL.Error:
                        pass
            except socket.error:
                pass  # some platforms may raise ENOTCONN here
            self.close_request(request)
        TCPServer.shutdown_request = my_shutdown_request


def setupNamespace(dbi):

    namespace = {'dbi': dbi}

    add(namespace, MaKaC, doc='MaKaC base package')
    add(namespace, Conference)
    add(namespace, Category)
    add(namespace, ConferenceHolder)
    add(namespace, CategoryManager)
    add(namespace, AvatarHolder)
    add(namespace, GroupHolder)
    add(namespace, HelperMaKaCInfo)
    add(namespace, PluginsHolder)
    add(namespace, Catalog)
    add(namespace, IndexesHolder)
    add(namespace, Config)

    add(namespace, HelperMaKaCInfo.getMaKaCInfoInstance(), 'minfo', 'MaKaCInfo instance')

    return namespace


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
    formatter = logging.Formatter("%(asctime)s %(name)-16s: %(levelname)-8s - %(message)s")
    logger = Logger.get()
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, level))
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def start_web_server(host='localhost', port=0, with_ssl=False, keep_base_url=True, ssl_cert=None, ssl_key=None,
                     reload_on_change=False):
    """
    Sets up a Werkzeug-based web server based on the parameters provided
    """

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
            base_url))
    default_port = 443 if with_ssl else 80
    url_data = urlparse.urlparse(base_url)

    # commandline data has priority, fallback to data from base url (or default in case of port)
    host = host or url_data.netloc.partition(':')[0]
    requested_port = used_port = port or url_data.port or default_port

    # Don't let people bind on a port they cannot use.
    if used_port < 1024 and not _can_bind_port(used_port):
        used_port += 8000
        console.warning(' * You cannot open a socket on port {0}, using {1} instead.'.format(requested_port, used_port))

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

    # If we need to perform internal requests for some reason we want to use the true host:port
    server_netloc = '{0}:{1}'.format(host, port) if port != default_port else host
    config._configVars['EmbeddedWebserverBaseURL'] = urlparse.urlunsplit(
        urlparse.urlsplit(base_url)._replace(netloc=server_netloc))

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
    # Regenerate JSVars to account for the updated URLs
    RHGetVarsJs.removeTmpVarsFile()

    console.info(' * Using BaseURL {0}'.format(base_url))
    app = make_indico_dispatcher(make_app())
    server = WerkzeugServer(app, host, used_port, reload_on_change=reload_on_change,
                            enable_ssl=with_ssl, ssl_cert=ssl_cert, ssl_key=ssl_key)
    signal.signal(signal.SIGINT, _sigint)
    server.run()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--logging', action='store',
                        help='display logging messages for specified level')

    parser.add_argument('--web-server', action='store_true',
                        help='run a standalone WSGI web server with Indico')
    parser.add_argument('--host',
                        help='use a different host than the one in indico.conf')
    parser.add_argument('--port', type=int,
                        help='use a different port than the one in indico.conf')
    parser.add_argument('--keep-base-url', action='store_true',
                        help='do not update the base url with the given host/port')

    parser.add_argument('--with-ssl', action='store_true',
                        help='enable ssl support for web server')
    parser.add_argument('--ssl-key', help='path to the ssl private key file')
    parser.add_argument('--ssl-cert', help='path to the ssl certificate file')
    parser.add_argument('--reload-on-change', action='store_true',
                        help='restart the server whenever a file changes (does not work for legacy code)')


    args, remainingArgs = parser.parse_known_args()

    if 'logging' in args and args.logging:
        setup_logging(args.logging)

    if 'web_server' in args and args.web_server:
        start_web_server(host=args.host,
                         port=args.port,
                         with_ssl=args.with_ssl,
                         keep_base_url=args.keep_base_url,
                         ssl_cert=args.ssl_cert,
                         ssl_key=args.ssl_key,
                         reload_on_change=args.reload_on_change)
    else:
        dbi = DBMgr.getInstance()
        dbi.startRequest()

        namespace = setupNamespace(dbi)

        if HAS_IPYTHON:
            if OLD_IPYTHON:
                ipshell = IPShellEmbed(remainingArgs,
                                       banner=SHELL_BANNER,
                                       exit_msg='Good luck',
                                       user_ns=namespace)
            else:
                config = IPConfig()
                config.TerminalInteractiveShell.confirm_exit = False
                ipshell = InteractiveShellEmbed(config=config,
                                                banner1=SHELL_BANNER,
                                                exit_msg='Good luck',
                                                user_ns=namespace)

            with make_app(True).app_context():
                ipshell()
        else:
            iconsole = code.InteractiveConsole(namespace)
            with make_app(True).app_context():
                iconsole.interact(SHELL_BANNER)

        dbi.abort()
        dbi.endRequest()
