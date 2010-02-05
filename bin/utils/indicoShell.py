import sys, getopt, logging

from IPython.Shell import IPShellEmbed

## MaKaC imported classes
import MaKaC
from MaKaC.common.db import DBMgr
from MaKaC.conference import Conference, Category, ConferenceHolder, CategoryManager, DeletedObjectHolder
from MaKaC.user import AvatarHolder, GroupHolder
from MaKaC.common.timerExec import HelperTaskList
from MaKaC.common.info import HelperMaKaCInfo
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

def addProductionElements(namespace):
    pedro = AvatarHolder().getById(22116)
    jose = AvatarHolder().getById(44)
    tiago = AvatarHolder().getById(26688)
    # admins
    add(namespace, pedro, 'pedro', 'Administrator #1')
    add(namespace, jose, 'jose', 'Administrator #2')
    # regular users
    add(namespace, tiago, 'tiago', 'Regular user #1')

def setupNamespace(productionDatabase):

    namespace = {'dbi': dbi}

    add(namespace, MaKaC, doc='MaKaC base package')
    add(namespace, Conference)
    add(namespace, Category)
    add(namespace, ConferenceHolder)
    add(namespace, DeletedObjectHolder)
    add(namespace, CategoryManager)
    add(namespace, AvatarHolder)
    add(namespace, GroupHolder)
    add(namespace, HelperTaskList)
    add(namespace, HelperMaKaCInfo)
    add(namespace, PluginsHolder)

    add(namespace, HelperMaKaCInfo.getMaKaCInfoInstance(), 'minfo', 'MaKaCInfo instance')

    if productionDatabase:
        addProductionElements(namespace)

    return namespace

if __name__ == '__main__':


    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='indicoShell.log',
                    filemode='w')


    productionDatabase = False

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "p", ["production-database"])
    except getopt.GetoptError, e:
        print str(e)
        sys.exit(2)

    for o, a in opts:
        if o in ('-p','--production-database'):
            productionDatabase = True

    dbi = DBMgr.getInstance()
    dbi.startRequest()

    namespace = setupNamespace(productionDatabase)

    ipshell = IPShellEmbed(args,
                           banner='Indico Shell',
                           exit_msg='Good luck',
                           user_ns = namespace)

    ipshell()
