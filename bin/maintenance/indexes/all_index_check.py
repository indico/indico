from MaKaC.common import DBMgr
from MaKaC.common.indexes import IndexesHolder
from indico.core.index import Catalog


if __name__ == '__main__':

    dbi = DBMgr.getInstance()

    dbi.startRequest()

    for idx_name in ['categ_conf_sd']:
        idx = Catalog.getIdx(idx_name)
        for problem in idx._check(dbi=dbi):
            print "[%s] %s" % (idx_name, problem)

    for idx_name in ['category', 'calendar', 'categoryDate']:
        idx = IndexesHolder().getIndex(idx_name)
        for problem in idx._check(dbi=dbi):
            print "[%s] %s" % (idx_name, problem)

    dbi.endRequest()
