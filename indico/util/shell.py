# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

import sys, getopt, logging, argparse, urlparse, re

from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler
from wsgiref.util import shift_path_info
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn

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

SHELL_BANNER = '\nindico %s\n' % MaKaC.__version__


def add(namespace, element, name=None, doc=None):

    if not name:
        name = element.__name__
    namespace[name] = element

    print "+ '%s'" % name,
    if doc:
        print ": %s" % doc
    else:
        print


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
     pass


class RefServer(object):

    def __init__(self, host='localhost', port=8000):
        """
        Run an Indico WSGI ref server instance
        Very simple dispatching app
        """

        config = Config.getInstance()

        baseURL = config.getBaseURL()
        path = urlparse.urlparse(baseURL)[2].rstrip('/')

        def fake_app(environ, start_response):
            rpath = environ['PATH_INFO']
            m = re.match(r'^%s(.*)$' % path, rpath)
            if m:
                environ['PATH_INFO'] = m.group(1)
                environ['SCRIPT_NAME'] = path
                for msg in application(environ, start_response):
                    yield msg
            else:
                start_response("404 NOT FOUND", [])
                yield 'Not found'

        self.httpd = make_server(host, port, fake_app,
                                 server_class=ThreadedWSGIServer,
                                 handler_class=WSGIRequestHandler)
        self.addr = self.httpd.socket.getsockname()

    def run(self):
        print "Serving at %s:%s..." % self.addr
        # Serve until process is killed
        self.httpd.serve_forever()


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

def main():
    formatter = logging.Formatter("%(asctime)s %(name)-16s: %(levelname)-8s - %(message)s")
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--logging', action='store',
                        help='display logging messages for specified level')

    parser.add_argument('--web-server', action='store_true',
                        help='run a standalone WSGI web server with Indico')

    args, remainingArgs = parser.parse_known_args()

    if 'logging' in args and args.logging:
        logger = Logger.get()
        handler = logging.StreamHandler()
        handler.setLevel(getattr(logging, args.logging))
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if 'web_server' in args and args.web_server:
        config = Config.getInstance()
        refserver = RefServer(config.getHostNameURL(), int(config.getPortURL()))
        refserver.run()
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
