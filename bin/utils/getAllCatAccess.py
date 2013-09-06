from indico.core.db import DBMgr
from MaKaC.user import Group, GroupHolder
from MaKaC.conference import CategoryManager
from MaKaC.webinterface.urlHandlers import UHCategoryDisplay, UHConferenceDisplay


def checkGroup (obj, group):
    ac = obj.getAccessController()
    if group in ac.allowed:
        return True
    return False

def showSubCategory(cat, group):
    if checkGroup(cat, group):
        print "%s - %s"%(cat.getName(), UHCategoryDisplay.getURL(cat))
    if cat.hasSubcategories():
        for subcat in cat.getSubCategoryList():
            showSubCategory(subcat,group)
    else:
        for conference in  cat.getConferenceList():
           if checkGroup(conference, group):
               print "%s - %s"%(conference.getName(), UHConferenceDisplay.getURL(conference))

DBMgr.getInstance().startRequest()
cm=CategoryManager()
cat=cm.getById("XXXX")
group = GroupHolder().getById("YYYYY")
showSubCategory(cat, group)


DBMgr.getInstance().endRequest()

