import sys, getopt, logging, argparse
from IPython.Shell import IPShellEmbed

## indico legacy imports
import MaKaC
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

    args, remainingArgs = parser.parse_known_args()

    if args.logging:
        logger = Logger.get()
        handler = logging.StreamHandler()
        handler.setLevel(getattr(logging, args.logging))
        handler.setFormatter(formatter)
        logger.addHandler(handler)

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
