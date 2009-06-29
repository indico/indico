from MaKaC.common import DBMgr
from MaKaC.user import Group
from MaKaC.conference import CategoryManager

DBMgr.getInstance().startRequest()
cm=CategoryManager()

catcounter = 0
mgrscounter = 0
notSendTo={}
catList=[]
rootCatList=[]
rootCatList.append(cm.getById('1l28'))
rootCatList.append(cm.getById('1l30'))
for cat in rootCatList:
    for scat in cat.getSubCategoryList():
        catList.append(scat)
    
for cat in catList:
    ml = cat.getManagerList()
    if ml:
        l=[]
        for mng in ml:
            if isinstance(mng, Group):
                if notSendTo.has_key(cat.getId()):
                    notSendTo[cat.getId()].append(mng.getName())
                else:
                    notSendTo[cat.getId()]=[]
                    notSendTo[cat.getId()].append(mng.getName())
            else:
                l.append(mng)
        mln = ", ".join(["%s <%s>"%(mng.getFullName(),mng.getEmail()) for mng in l])
        print "[%s]%s\n\t--> [%s]\n"%(cat.getId(), cat.getTitle(), mln)
        catcounter += 1
        mgrscounter += len(ml)
print "%s categories with managers. There is a total of %s managers"%(catcounter, mgrscounter)
print "not send to:%s"%notSendTo
DBMgr.getInstance().endRequest()

