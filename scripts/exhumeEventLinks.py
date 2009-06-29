from MaKaC.common import DBMgr
from MaKaC import user
from MaKaC import conference

import traceback

curper = -1
fixes = 0

def percent_show(fraction, total):
    global curper
    
    per = int(float(fraction)/float(total)*100)
    
    if per != curper:
        print "%d%% %d/%d" % (per, fraction, total)
        curper = per

def exhumeLinks(avatarHolder, conf):
    
    global fixes
    
    conf.getCreator().linkTo(conf, "creator")
    
    for participant in conf.getParticipation().getParticipantList():
        
        avatar = participant.getAvatar()
        
        if avatar:
            avatar.linkTo(conf, "participant")
            fixes += 1
        
    registrants = conf.getRegistrants()
    for regIdx in registrants:
        avatar = registrants[regIdx].getAvatar()
        
        if avatar:
            registrants[regIdx].getAvatar().linkTo(registrants[regIdx], "registrant")
            fixes += 1
                
    for manager in conf.getManagerList():
        
        if type(manager) == user.Avatar:
            manager.linkTo(conf, "manager")
            fixes += 1
        
try:
    DBMgr.getInstance().startRequest()

    ah = user.AvatarHolder()
    ch = conference.ConferenceHolder()
    list = ch.getList()

    totalConfs = len(list)

    print totalConfs,'registers'

    count = 0;

    for conf in ch.getList():
        count += 1        
        percent_show(count, totalConfs);
        exhumeLinks(ah,conf)
        
        DBMgr.getInstance().commit()
        DBMgr.getInstance().sync()
        
    DBMgr.getInstance().endRequest()
    
    print "%d fixes done" % fixes
    
except Exception,e:
    print 'Exception:',e
    traceback.print_exc()