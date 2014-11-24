from __future__ import division

from collections import Counter

from indico.core.db import DBMgr
from indico.util.console import conferenceHolderIterator, success
from MaKaC.conference import ConferenceHolder
from MaKaC.webinterface.displayMgr import ConfDisplayMgrRegistery


def update_menus(dbi):
    links = ('collaboration', 'downloadETicket', 'ViewMyRegistration', 'NewRegistration')
    ch = ConferenceHolder()
    cdmr = ConfDisplayMgrRegistery()
    counter = Counter()

    for __, event in conferenceHolderIterator(ch, deepness='event'):
        menu = cdmr.getDisplayMgr(event).getMenu()
        must_update = False
        for linkname in links:
            if menu.getLinkByName(linkname) is None:
                counter[linkname] += 1
                must_update = True
        if must_update:
            menu.updateSystemLink()
            counter['updated'] += 1
        if counter['updated'] % 100:
            dbi.commit()

    for linkname in links:
        print "{} links missing: {}".format(linkname, counter[linkname])
    success("Event menus updated: {}".format(counter['updated']))


if __name__ == '__main__':
    dbi = DBMgr.getInstance()
    dbi.startRequest()
    update_menus(dbi)
    dbi.endRequest()
