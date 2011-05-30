from MaKaC.common.db import DBMgr
from MaKaC.conference import CategoryManager


i = 0


def _visit(dbi, cat):
    global i
    if not cat.getConferenceList():
        for scat in cat.getSubCategoryList():
            _visit(dbi, scat)
        cat._setNumConferences()
        print "set %s: %s" % (cat.getTitle(), cat.getNumConferences())

    if i % 99 == 0:
        dbi.commit()
    i += 1


if __name__ == '__main__':
    dbi = DBMgr.getInstance()
    dbi.startRequest()
    home = CategoryManager().getById(0)

    with dbi.transaction() as conn:
        i = 0
        _visit(dbi, home)
