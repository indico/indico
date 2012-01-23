import sys, getopt, logging, argparse, urlparse, re
from IPython.Shell import IPShellEmbed
from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler
from wsgiref.util import shift_path_info
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn

from indico.web.wsgi.indico_wsgi_handler import application

## indico legacy imports
import MaKaC
from MaKaC.common import Config
from MaKaC.common.db import DBMgr
from MaKaC.conference import Conference, Category, ConferenceHolder, CategoryManager
from MaKaC.user import AvatarHolder, GroupHolder
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.logger import Logger
from MaKaC.plugins.base import PluginsHolder


def add(namespace, element, name=None, doc=None):

    if not name:
        name = element.__name__
    namespace[name] = element

    print "Added '%s'" % name,
    if doc:
        print ": %s" % doc
    else:
        print


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
     pass

def refServer(host='localhost', port=8000):
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

    print "Serving on port %d..." % port
    httpd = make_server(host, port, fake_app,
                        server_class=ThreadedWSGIServer,
                        handler_class=WSGIRequestHandler)
    # Serve until process is killed
    httpd.serve_forever()


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
        refServer(config.getHostNameURL(), int(config.getPortURL()))
    else:
        dbi = DBMgr.getInstance()
        dbi.startRequest()

        namespace = setupNamespace(dbi)

        ipshell = IPShellEmbed(remainingArgs,
                               banner='Indico Shell',
                               exit_msg='Good luck',
                               user_ns=namespace)

        ipshell()

        dbi.abort()
        dbi.endRequest()
