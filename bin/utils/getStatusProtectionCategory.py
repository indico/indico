from MaKaC.common import DBMgr
from MaKaC.user import Group
from MaKaC.conference import CategoryManager, Conference, Category

DBMgr.getInstance().startRequest()
cm=CategoryManager()

cat=cm.getById('2l76')
conferences= cat.getAllConferenceList()
f = open("statusProtection.txt","w")
for conference in conferences:
    f.write(conference.getId() + " " + conference.getTitle() + " " + str(conference.isItselfProtected()) + " " + str(conference.isProtected())  + "\n")
f.close()
DBMgr.getInstance().endRequest()

