# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
import re
import socket
import sys
from SocketServer import TCPServer

try:
    import werkzeug.serving
except ImportError:
    werkzeug = None

try:
    from OpenSSL import SSL
except ImportError:
    SSL = None

from indico.web.wsgi.indico_wsgi_handler import application
from indico.core.index import Catalog

## indico legacy imports
import MaKaC
from MaKaC.common import Config
from MaKaC.common.db import DBMgr
from MaKaC.conference import Conference, Category, ConferenceHolder, CategoryManager
from MaKaC.user import AvatarHolder, GroupHolder
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.indexes import IndexesHolder
from MaKaC.common.logger import Logger
from MaKaC.plugins.base import PluginsHolder

try:
    HAS_IPYTHON = True
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

SHELL_BANNER = '\nindico {0}\n'.format(MaKaC.__version__)


def add(namespace, element, name=None, doc=None):

    if not name:
        name = element.__name__
    namespace[name] = element

    if doc:
        print '+ {0} : {1}'.format(name, doc)
    else:
        print '+ {0}'.format(name)


class WerkzeugServer(object):

    def __init__(self, host='localhost', port=8000, enable_ssl=False, ssl_key=None, ssl_cert=None):
        """
        Run an Indico WSGI ref server instance
        Very simple dispatching app
        """

        if not werkzeug:
            print 'Please install werkzeug to use the builtin dev server'
            sys.exit(1)
        elif not SSL and enable_ssl:
            print 'You need pyopenssl to use SSL'
            sys.exit(1)

        config = Config.getInstance()

        baseURL = config.getBaseURL()
        path = urlparse.urlparse(baseURL)[2].rstrip('/')

        def fake_app(environ, start_response):
            rpath = environ['PATH_INFO']
            m = re.match(r'^{0}(.*)$'.format(path), rpath)
            if m:
                environ['PATH_INFO'] = m.group(1)
                environ['SCRIPT_NAME'] = path
                for msg in application(environ, start_response):
                    yield msg
            else:
                start_response("404 NOT FOUND", [])
                yield 'Not found'

        self.app = fake_app
        self.host = host
        self.port = port
        self.ssl = enable_ssl
        self.ssl_key = ssl_key
        self.ssl_cert = ssl_cert

        logger = logging.getLogger('werkzeug')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler(sys.stderr))

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

    def run(self):
        if not self.ssl:
            ssl_context = None
        elif not self.ssl_cert and not self.ssl_key:
            self._patch_shutdown_request()
            ssl_context = 'adhoc'
        else:
            self._patch_shutdown_request()
            ssl_context = SSL.Context(SSL.SSLv23_METHOD)
            ssl_context.use_privatekey_file(self.ssl_key)
            ssl_context.use_certificate_chain_file(self.ssl_cert)
        # In case anyone wonders why evalex is disabled:
        # 1. It's a huge security hole when open to the public. To use it properly we'd need a way to
        #    restrict it by IP address (or disable it when not listening on localhost)
        # 2. ZODB uses a thread-local field to store the connection. So anything accessing the DB will not work
        #    when accessed from the debugger shell.
        # So the best solution is not using that part of the werkzeug debugger at all.
        # Simply use e.g. pydev or rpdb2 if you want a debugger.
        werkzeug.serving.run_simple(self.host, self.port, self.app, threaded=True, ssl_context=ssl_context,
                                    use_debugger=True, use_evalex=False)


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


def main():
    formatter = logging.Formatter("%(asctime)s %(name)-16s: %(levelname)-8s - %(message)s")
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


    args, remainingArgs = parser.parse_known_args()

    if 'logging' in args and args.logging:
        logger = Logger.get()
        handler = logging.StreamHandler()
        handler.setLevel(getattr(logging, args.logging))
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if 'web_server' in args and args.web_server:
        config = Config.getInstance()
        # Let Indico know that we are using the embedded server. This causes it to re-raise exceptions so they
        # end up in the Werkzeug debugger.
        config._configVars['EmbeddedWebserver'] = True
        # Get appropriate base url and defaults
        base_url = config.getBaseSecureURL() if args.with_ssl else config.getBaseURL()
        if not base_url:
            base_url = config.getBaseURL() or 'http://localhost'
            print ' * You should set {0}; falling back to {1}'.format(
                'BaseSecureURL' if args.with_ssl else 'BaseURL',
                base_url)
        default_port = 443 if args.with_ssl else 80
        url_data = urlparse.urlparse(base_url)
        # commandline data has priority, fallback to data from base url (or default in case of port)
        host = args.host or url_data.netloc.partition(':')[0]
        requested_port = port = args.port or url_data.port or default_port
        # Don't let people bind on a port they cannot use.
        if port < 1024 and not _can_bind_port(port):
            port += 8000
            print ' * You cannot open a socket on port {0}, using {1} instead.'.format(requested_port, port)
        # By default we update the base URL with the actual host/port. The user has the option to
        # disable this though in case he wants different values, e.g. to use iptables to make his
        # development server available via port 443 while listening on a non-privileged port:
        # iptables -t nat -A PREROUTING -d YOURIP/32 -p tcp -m tcp --dport 443 -j REDIRECT --to-port 8443
        if not args.keep_base_url:
            scheme = 'https' if args.with_ssl else 'http'
            netloc = host
            if port != default_port:
                netloc += ':{0}'.format(port)
            base_url = '{0}://{1}{2}'.format(scheme, netloc, url_data.path)
        # However, if we had to change the port to avoid a permission issue we always rewrite BaseURL.
        # In this case it is somewhat safe to assume that the user is not actually trying to use the iptables hack
        # mentioned above but simply did not consider using a non-privileged port.
        elif requested_port != port:
            netloc = '{0}:{1}'.format(url_data.netloc.partition(':')[0], port)
            base_url = '{0}://{1}{2}'.format(url_data.scheme, netloc, url_data.path)

        # We update both BaseURL and BaseSecureURL to something that actually works.
        # In case of SSL-only we need both URLs to be set to the same SSL url to prevent some stuff being "loaded"
        # from an URL that is not available.
        # In case of not using SSL we clear the BaseSecureURL so the user does not need to update the config during
        # development if he needs to disable SSL for some reason.
        if args.with_ssl:
            config._configVars['BaseURL'] = base_url
            config._configVars['BaseSecureURL'] = base_url
        else:
            config._configVars['BaseURL'] = base_url
            config._configVars['BaseSecureURL'] = ''
        config._deriveOptions()

        print ' * Using BaseURL ' + base_url
        server = WerkzeugServer(host, port, enable_ssl=args.with_ssl,
                                ssl_cert=args.ssl_cert, ssl_key=args.ssl_key)
        server.run()
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
                ipshell = InteractiveShellEmbed(config=config,
                                            banner1=SHELL_BANNER,
                                            exit_msg='Good luck',
                                            user_ns=namespace)

            ipshell()
        else:
            console = code.InteractiveConsole(namespace)
            console.interact(SHELL_BANNER)

        dbi.abort()
        dbi.endRequest()
