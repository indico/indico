from MaKaC.common import DBMgr
from MaKaC import user
from MaKaC import conference

curper = -1
fixes = 0

def percent_show(fraction, total):
    global curper
    
    per = int(float(fraction)/float(total)*100)
    
    if per != curper:
        print "%d%% %d/%d" % (per, fraction, total)
        curper = per

def fixLinks(confHolder, user):
    
    linkedTo = user.getLinkedTo()
    
    global fixes
    
    # Assure that all the linked conferences exist
    creators = linkedTo['conference']
    
    for confRole in creators:
        for conf in creators[confRole]:
            try:                
                confHolder.getById(conf.getId())
            except:
                creators[confRole].remove(conf)
                fixes += 1
    
    registrants = linkedTo['registration']
    
    for registrantRole in registrants:
        for reg in registrants[registrantRole]:
            try:
                confHolder.getById(reg.getConference().getId())
            except:
                registrants[registrantRole].remove(reg)
                fixes += 1
    
    # rebuild the TLE table
    user.resetTimedLinkedEvents()
    
try:
    DBMgr.getInstance().startRequest()

    ah = user.AvatarHolder()
    ch = conference.ConferenceHolder()
    list = ah.getList()

    totalUsers = len(list)

    print totalUsers,'registers'

    count = 0;

    for user in ah.getList():
        count += 1        
        percent_show(count, totalUsers);
        try:
           user.timedLinkedEvents
           fixLinks(ch,user)
           DBMgr.getInstance().savepoint()
           DBMgr.getInstance().sync()

        except AttributeError:
            pass
        
    DBMgr.getInstance().endRequest()
    
    print "%d fixes done" % fixes
    
except Exception,e:
    print 'Exception:',e