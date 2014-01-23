# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.


# This script has to be run after an upgrade to Indico v0.96
# Make sure you have set your default server timezone through the web interface
# before running this script
# If you did not the server timezone will be defaulted to 'UTC'
# This script will convert all dates in the database to UTC dates, using the
# default server timezone as origin of the conversion.

import os,shutil
from indico.core.db import DBMgr
import MaKaC.common.info as info
from pytz import timezone,common_timezones
from MaKaC.conference import CategoryManager, ConferenceHolder, DeletedObjectHolder
from MaKaC.user import AvatarHolder
from MaKaC.common import indexes, timerExec
from datetime import datetime
import MaKaC.common.indexes as indexes
from time import sleep
from indico.core.config import Config

LOG_FILE = ""
logfile = None
catTZMap = {}
CAT_TZ_FILE = ""

def log(msg):
    global logfile
    if logfile == None:
        logfile=open(LOG_FILE,"w")
    print msg
    logfile.write("%s\n"%msg)

def getCatTZMap():
    global CAT_TZ_FILE
    global catTZMap
    if CAT_TZ_FILE == "":
        CAT_TZ_FILE = raw_input("\n\nPlease enter the name of the file containing the category/timezone mapping: ")
    f=file(CAT_TZ_FILE, 'r')
    for line in f.readlines():
        line=line.strip()
        if line != "":
            v=line.split("\t")
            if len(v)==2:
                catTZMap[v[0]] = v[1]


def date2txt(date):
    return date.strftime("%Y-%m-%d")

def updateOAIIndexes():
    DBMgr.getInstance().startRequest()
    ch = ConferenceHolder()
    ih = indexes.IndexesHolder()
    catIdx = ih.getById("category")
    confIdx = ih.getById("OAIConferenceModificationDate")
    contIdx = ih.getById("OAIContributionModificationDate")
    confIdxPr = ih.getById("OAIPrivateConferenceModificationDate")
    contIdxPr = ih.getById("OAIPrivateContributionModificationDate")
    confIdx.initIndex()
    contIdx.initIndex()
    confIdxPr.initIndex()
    contIdxPr.initIndex()
    DBMgr.getInstance().commit()
    log("Count conferences...")
    ids = catIdx.getItems('0')
    totalConf = len(ids)
    log("%d conferences found"%totalConf)
    ic = 1
    DBMgr.getInstance().sync()
    DBMgr.getInstance().endRequest()
    i = 0
    pubConf = 0
    privConf = 0
    while ids:
        if len(ids) >= 10:
            lids = ids[:10]
            del ids[:10]
        else:
            lids = ids
            ids = None
        startic = ic
        startPubConf = pubConf
        startPrivConf = privConf
        for j in range(10):
            try:
                DBMgr.getInstance().startRequest()
                for id in lids:
                    conf = ch.getById(id)
                    confIdx = ih.getById("OAIConferenceModificationDate")
                    contIdx = ih.getById("OAIContributionModificationDate")
                    confIdxPr = ih.getById("OAIPrivateConferenceModificationDate")
                    contIdxPr = ih.getById("OAIPrivateContributionModificationDate")
                    log("Index conference %s: %d on %d"%(id, ic, totalConf))
                    ic += 1
                    if conf.hasAnyProtection():
                        confIdxPr.indexConference(conf)
                        privConf += 1
                    else:
                        confIdx.indexConference(conf)
                        pubConf += 1
                    for cont in conf.getContributionList():
                        if cont.hasAnyProtection():
                            contIdxPr.indexContribution(cont)
                        else:
                            contIdx.indexContribution(cont)
                        for sc in cont.getSubContributionList():
                            if cont.isProtected():
                                contIdxPr.indexContribution(sc)
                            else:
                                contIdx.indexContribution(sc)
                DBMgr.getInstance().endRequest()
                log("wait 0.5s...")
                sleep(0.5)
                break
            except Exception, e:
                log("error %s, retry %d time(s)"%(e,int(10-j)))
                sleep(int(j))
                ic = startic
                pubConf = startPubConf
                privConf = startPrivConf
                DBMgr.getInstance().abort()
    log("Indexed conferences : %d public, %d private"%(pubConf, privConf))

    log("Index deleted conference and contribution...")
    try:
        DBMgr.getInstance().startRequest()
        doh = DeletedObjectHolder()
        doh.initIndexes()
        for obj in doh.getAll():
            obj.index()
        DBMgr.getInstance().endRequest()
        log("Deleted conference and contribution Indexed")
    except Exception,e:
        log("Error %s: Deleted conference and contribution not indexed"%e)



def updateCalendarIndex():
    DBMgr.getInstance().startRequest()
    im = indexes.IndexesHolder()
    im.removeById('calendar')
    DBMgr.getInstance().commit()
    ch = CategoryManager()
    list = ch.getList()
    totnum = len(list)
    curnum = 0
    curper = 0
    for cat in list:
        committed = False
        DBMgr.getInstance().sync()
        calindex = im.getIndex('calendar')
        while not committed:
            try:
                del cat._calIdx
            except:
                pass
            for conf in cat.getConferenceList():
                try:
                    calindex.indexConf(conf)
                except Exception,e:
                    log("%s"%e)
                    log("calindex: exception indexing [%s] sd:%s, ed:%s"%(conf.getId(),conf.getStartDate(), conf.getEndDate()))
            try:
                DBMgr.getInstance().commit()
                committed = True
            except:
                DBMgr.getInstance().abort()
                log("retry %s" % cat.getId())
        curnum += 1
        per = int(float(curnum)/float(totnum)*100)
        if per != curper:
            curper = per
            if per in [0,10,20,30,40,50,60,70,80,90,100]:
                log("done %s%%" % per)
    DBMgr.getInstance().endRequest()

def hasTZ( date ):
    if not date.tzinfo:
        return False
    return True

def chDate( date, tz=None):
    if not tz:
        tz = defTZ
    if not date:
        return None
    if not hasTZ(date):
        date = timezone(tz).localize(date).astimezone(timezone('UTC'))
    return date

def updateSchedule( sch, tz=None ):
    if not tz:
        tz = defTZ
    if sch:
        try:
            if sch._startDate is not None:
                sch._startDate = chDate(sch._startDate, tz)
        except:
            pass
        try:
            if sch._endDate is not None:
                sch._endDate = chDate(sch._endDate, tz)
        except:
            pass
        for entry in sch.getEntries():
            updateSchEntry(entry, tz)

def updateSchEntry( en , tz=None):
    if not tz:
        tz = defTZ
    try:
        en.startDate = chDate(en.startDate, tz)
    except:
        pass

def updateEventDates( conf , tz=None):
    if not tz:
        tz = defTZ
    conf.startDate = chDate(conf.startDate, tz)
    conf.endDate = chDate(conf.endDate, tz)
    conf._creationDS = chDate(conf._creationDS, tz)
    conf._modificationDS = chDate(conf._modificationDS, tz)
    try:
        conf._screenStartDate = chDate(conf._screenStartDate, tz)
    except:
        pass
    try:
        conf._screenEndDate = chDate(conf._screenEndDate, tz)
    except:
        pass
    try:
        conf._archivingDate = chDate(conf._archivingDate, tz)
    except:
        pass
    try:
        conf._submissionDate = chDate(conf._submissionDate, tz)
    except:
        pass
    try:
        conf._archivingRequestDate = chDate(conf._archivingRequestDate, tz)
    except:
        pass

def updateTask( task ):
    try:
        task.startDate = chDate(task.startDate,defTZ)
    except:
        pass
    try:
        task.endDate = chDate(task.endDate,defTZ)
    except:
        pass
    try:
        task.lastDate = chDate(task.lastDate,defTZ)
    except:
        pass

def updateAbstractMgr( am, tz=None ):
    if not tz:
        tz = defTZ
    for abs in am.getAbstractList():
        updateAbstract(abs, tz)

def updateAbstract( abs, tz = None ):
    if not tz:
        tz = defTZ
    try:
        abs._modificationDate = chDate(abs._modificationDate, tz)
    except:
        pass
    try:
        abs._submissionDate = chDate(abs._submissionDate, tz)
    except:
        pass
    try:
        abs.getCurrentStatus()._date = chDate(abs.getCurrentStatus()._date, tz)
    except:
        pass
    for track in abs.getTrackListSorted():
        judg = abs.getTrackJudgement(track)
        try:
            judg._date = chDate(judg._date, tz)
        except:
            pass
    for entry in abs.getNotificationLog().getEntryList():
        entry._date = chDate(entry._date, tz)
    for intComment in abs.getIntCommentList():
        intComment._creationDate = chDate(intComment._creationDate, tz)
        intComment._modificationDate = chDate(intComment._modificationDate, tz)

def updateContribution( cont , tz=None):
    if not tz:
        tz = defTZ
    cont.startDate = chDate(cont.startDate, tz)
    cont._OAImodificationDS = chDate(cont.getOAIModificationDate(), tz)
    try:
        cont._modificationDS = chDate(cont._modificationDS, tz)
    except:
        pass
    try:
        cont._archivingDate = chDate(cont._archivingDate, tz)
    except:
        pass
    try:
        cont.getCurrentStatus()._date = chDate(cont.getCurrentStatus()._date, tz)
    except:
        pass

def updateLogHandler(lh):
    for li in lh.getEmailLogList():
        li._logDate = chDate(li._logDate, defTZ)
    for li in lh.getActionLogList():
        li._logDate = chDate(li._logDate, defTZ)
    for li in lh.getGeneralLogList():
        li._logDate = chDate(li._logDate, defTZ)

def updateEvent( conf, tz=None ):
    if not tz:
        tz = defTZ
    conf.setTimezone(tz)
    conf._OAImodificationDS = chDate(conf.getOAIModificationDate(),defTZ)
    updateEventDates( conf, tz )
    updateSchedule( conf.getSchedule(), tz )
    #sessions
    for ses in conf.getSessionList():
        ses.startDate = chDate(ses.startDate,tz)
        updateSchedule( ses.getSchedule(), tz )
        for slot in ses.getSlotList():
            slot.startDate = chDate(slot.startDate, tz)
            updateSchedule( slot.getSchedule(), tz )
    for cont in conf.getContributionList():
        updateContribution( cont, tz )
    updateAbstractMgr(conf.getAbstractMgr(), tz)
    updateLogHandler(conf.getLogHandler())
    updateRegistrants(conf.getRegistrantsList())

def updateRegistrants(reglist):
    for reg in reglist:
        try:
            reg._registrationDate = chDate(reg._registrationDate)
        except:
            pass

def updateCatTasks(cat):
    for task in cat.getTaskList():
        task._creationDate = chDate(task._creationDate, defTZ)
        commhist = task.getCommentHistoryElements()[:]
        task._commentHistory = {}
        for comm in commhist:
            comm._creationDate = chDate(comm._creationDate, defTZ)
            task._commentHistory["%s"%comm.getCreationDate()] = comm
        stathist = task.getStatusHistory().values()[:]
        task._statusHistory = {}
        for st in stathist:
            st._settingDate = chDate(st._settingDate, defTZ)
            task._statusHistory["%s"%st.getSettingDate()] = st
        task.notifyModification()

def updateCategsAndEvents():

    DBMgr.getInstance().startRequest()
    cm = CategoryManager()
    l = [cat.getId() for cat in cm.getList()]
    DBMgr.getInstance().endRequest()
    for id in l:
        DBMgr.getInstance().startRequest()
        cat = cm.getById(id)
        log("\nupdate category %s:%s"%(cat.getId(), cat.getName()))
        if cat.getId() in catTZMap.keys() and catTZMap[cat.getId()] :
            tz = catTZMap[cat.getId()]
            log("    found tz for this category: %s"%tz)
        else:
            tz = defTZ
            log("    use default tz: %s"%tz)
        cat.setTimezone(tz)
        updateCatTasks(cat)
        for conf in cat.getConferenceList():
            updateEvent(conf, tz)
            log("  conf %s: %s updated with tz: %s"%(conf.getId(), conf.getTitle(), tz))
        DBMgr.getInstance().endRequest()

def updateUserDef( user ):
    user.setTimezone()
    user.setDisplayTZMode()

def cleanCache():
    """ removes an entire cache directory"""
    path = os.path.join(Config().getInstance().getXMLCacheDir(), "categories")
    if os.path.exists(path):
        shutil.rmtree(path)
    path = os.path.join(Config().getInstance().getXMLCacheDir(), "events")
    if os.path.exists(path):
        shutil.rmtree(path)

if LOG_FILE == "":
    LOG_FILE = raw_input("\n\nPlease enter a filename (absolute path) for logging: ")

getCatTZMap()

DBMgr.getInstance().startRequest()

#defTZ = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
d = {}
for i in common_timezones:
    if i in ['GMT','UTC']:
        d[i]=i
    else:
        atoms = i.split('/')
        if len(atoms) == 2:
            cont,town = atoms
        else:
            cont,town = atoms[0], "%s/%s" % (atoms[1],atoms[2])
        if cont in d.keys():
            d[cont].append(i)
        else:
            d[cont] = [i]
cont = ""
while not cont in d.keys():
    for i in d.keys():
        log(i)
    cont = raw_input("Enter the country/continent of the server:")

defTZ = ""
while not defTZ in d[cont]:
    for i in d[cont]:
        log(i)
    defTZ = raw_input("Enter the timezone of the server:")

log("set default server timezone: %s" % defTZ)
info.HelperMaKaCInfo.getMaKaCInfoInstance().setTimezone(defTZ)

log("start: %s" % str(datetime.now()))

execute = [ 1, 2, 3, 4, 5, 6, 7 ]
#execute = [ 1, 3, 4, 5, 6, 7 ]
#execute = [ 6, 7 ]

# update all users defaults
if 1 in execute:
    log("step 1/7: update users")
    for us in AvatarHolder().getList():
        updateUserDef( us )
        DBMgr.getInstance().commit()

# update all event dates
if 3 in execute:
##    log("step 3/7: update all events")
##    events = ConferenceHolder().getList()
##    totnum = len(events)
##    curnum = 0
##    curper = 0
##    for ev in events:
##        #if not ev.startDate.tzinfo:
##        updateEvent(ev)
##        DBMgr.getInstance().commit()
##        curnum += 1
##        per = int(float(curnum)/float(totnum)*100)
##        if per != curper:
##            curper = per
##            if per in [0,10,20,30,40,50,60,70,80,90,100]:
##                log("done %s%%" % per    )
    DBMgr.getInstance().endRequest()
    log("step 3/7: update all categories and events")
    updateCategsAndEvents()
    DBMgr.getInstance().startRequest()

# update tasks
if 4 in execute:
    log("step 4/7: update tasks")
    htl = timerExec.HelperTaskList.getTaskListInstance()
    for task in htl.getTasks():
        updateTask(task)
    DBMgr.getInstance().commit()

if 'special' in execute:
    ev = ConferenceHolder().getById('10235')
    updateEvent(ev)
    DBMgr.getInstance().commit()

DBMgr.getInstance().endRequest()

# reindex OAI
if 5 in execute:
    log("step 5/7: rebuild OAI index")
    updateOAIIndexes()

DBMgr.getInstance().startRequest()
# update default conference dates
if 2 in execute:
    log("step 2/7: update default event")
    defConf = CategoryManager().getDefaultConference()
    updateEvent(defConf)
    DBMgr.getInstance().commit()
DBMgr.getInstance().endRequest()

# reindex cal
if 6 in execute:
    log("step 6/7: rebuild calendar index")
    updateCalendarIndex()

#clean cache
if 7 in execute:
    log("step 7/7: clean cache")
    cleanCache()
log("end: %s" % str(datetime.now()))

