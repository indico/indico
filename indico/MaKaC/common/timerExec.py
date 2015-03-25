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
from indico.util.i18n import i18nformat

import time, signal, copy, sys, traceback
from threading import Thread
import smtplib
from datetime import datetime, timedelta

import ZODB
from persistent import Persistent
from BTrees import OOBTree

from MaKaC.common.db import DBMgr
import os
from Configuration import Config
from MaKaC.common.info import HelperMaKaCInfo
from Counter import Counter
from MaKaC.user import Avatar
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.common.contextManager import ContextManager
from MaKaC.statistics import CategoryStatistics
from MaKaC.webinterface.mail import GenericMailer, GenericNotification
from MaKaC.trashCan import TrashCanManager
from MaKaC.i18n import _
from pytz import timezone
from pytz import all_timezones

from MaKaC.rb_location import CrossLocationDB

class toExec:
    """
    Get the list of task and for each one, check if its time to run it
    """
    def __init__(self, logFilename=None):
        self._file=None
        self._logFilename=logFilename

    def _initLog(self):
        if self._logFilename:
            i = 0
            while i < 10:
                try:
                    self._file=open(self._logFilename,"a")
                    i = 11
                except IOError, e:
                    if i < 10:
                        i += 1
                        time.sleep(i)
                    else:
                        self._printOutput(e)
                        raise

    def _closeLog(self):
        if self._file:
            self._file.close()

    def _printOutput(self, text):
        text = "[%s] %s"%(id(self),text)
        if self._logFilename:
            if self._file:
                print >> self._file, text
                self._file.flush()
                return
        print text

    def _runObj(self, obj):
        # create the context
        ContextManager.create()

        try:
            obj.run()
        except Exception, e:
            self._printOutput(e)
            self._sendErrorEmail(e)

        # destroy the context
        ContextManager.destroy()


    def execute(self):
        try:
            self._initLog()
            self._printOutput("***Starting execute***\n")
            ### Get the connection in order to avoid that to threads share the same one
            conn = DBMgr().getInstance()
            conn.startRequest()

            minfo = HelperMaKaCInfo.getMaKaCInfoInstance()

            if minfo.getRoomBookingModuleActive():
                CrossLocationDB.connect()
            ###
            taskList = HelperTaskList().getTaskListInstance()
            tasks = taskList.getTasks()
            if len(tasks) == 0:
                self._printOutput("--->No tasks!")
            else:
                self._printOutput("Execute at %s\n"%datetime.now())
            taskids = [i.getId() for i in tasks]
            for id in taskids:
                ### check if another thread have already removed the task
                conn.sync()
                if not id in taskList.listTask.keys():
                    continue
                task = taskList.getTaskById(id)
                ###
                if task.isRunning():
                    self._printOutput("\t--->Task <%s> already running"%task.getId())
                else:
                    try:
                        self._printOutput("\t--->Running task <%s>"%task.getId())

                        if task.getStartDate() == None or task.getStartDate() < nowutc():
                            self._printOutput("\t (SINGLE RUN)")
                            # the task is started
                            if task.getInterval() == None or task.getLastDate() == None:
                                # the task is run once or never runned
                                task.setRunning(True)
                                conn.commit()
                                abort=task.prerun()
                                if abort:
                                    self._printOutput("\t<---Task <%s> was aborted."%task.getId())
                                    task.setRunning(False)
                                    conn.commit()
                                    continue
                                for obj in task.getObjList():
                                    self._printOutput("\t\tRunning object <%s> (start date: %s)"%(obj.getId(),task.getStartDate()))
                                    #task.setLastDate(datetime.now())

                                    self._runObj(obj)

                                    self._printOutput("\t\tEnd object")
                                task.setLastDate(nowutc())
                                task.setRunning(False)
                                if task.getInterval() == None:
                                    # if run once, delete the task from list
                                    taskList.removeTask(task)
                                    self._printOutput("\t\tTask was removed")
                                else:
                                    self._printOutput("\t\tTask is periodic (getInterval: %s)" % task.getInterval())
                            else:
                                self._printOutput("\t (PERIODIC TASK)")
                                # the task is to be run multiple times
                                if task.getLastDate() + task.getInterval() < nowutc():
                                    task.setRunning(True)
                                    conn.commit()
                                    abort=task.prerun()
                                    if abort:
                                        self._printOutput("\t<---Task <%s> was aborted."%task.getId())
                                        task.setRunning(False)
                                        conn.commit()
                                        continue
                                    # it's time to launch the task!!!
                                    for obj in task.getObjList():
                                        self._printOutput("\tRunning object %s (last date: %s)"%(obj.getId(),task.getLastDate()))
                                        #task.setLastDate(datetime.now())

                                        self._runObj(obj)

                                        self._printOutput("\t\tEnd object")
                                    if task.getLastDate() and task.getEndDate():
                                        if task.getLastDate() + task.getInterval() > task.getEndDate():
                                            # the task is finish, delete it from list
                                            taskList.removeTask(task)
                                            self._printOutput("\t\tTask was removed")
                                    task.setLastDate(nowutc())
                                    task.setRunning(False)
                        self._printOutput("\t<---end task <%s>\n"%task.getId())
                        conn.commit()
                    except Exception, e:
                        conn.sync()
                        task.setRunning(False)
                        conn.commit()
                        ty, ex, tb = sys.exc_info()
                        tracebackList = traceback.format_list( traceback.extract_tb( tb ) )
                        self._printOutput("*****---->[ERROR]:%s\nTraceback:%s"%(e,"\n".join(tracebackList)))
                        self._sendErrorEmail(e)

            if minfo.getRoomBookingModuleActive():
                CrossLocationDB.commit()
                CrossLocationDB.disconnect()

            conn.endRequest()

            self._printOutput("***end execute***\n\n")
            self._closeLog()
        except Exception, e:
            ty, ex, tb = sys.exc_info()

            tracebackList = traceback.format_list( traceback.extract_tb( tb ) )
            self._printOutput("*****---->[ERROR]:%s\nTraceback:%s"%(e,"\n".join(tracebackList)))
            self._sendErrorEmail(e)

    def _sendErrorEmail(self, e):
        ty, ex, tb = sys.exc_info()
        tracebackList = traceback.format_list( traceback.extract_tb( tb ) )
        sm = sendMail()
        sm.setFromAddr(Config.getInstance().getSupportEmail())
        sm.addToAddr(Config.getInstance().getSupportEmail())
        sm.setSubject("[Indico] Error running a task")
        sm.setText("""

                    - Details of the exception:
                        %s

                    - Traceback:

                        %s

                    --

                    <Indico support> indico-project @ cern.ch
                    """%(e, "\n".join( tracebackList )) )
        sm.run()

class taskList(Persistent):
    """
    Persistant class which keep the list of task to do
    """
    def __init__(self):
        self.listTask = {}
        self._taskGenerator = Counter()

    def getTasks(self):
        return self.listTask.values()

    def addTask(self, task):
        id = task.getId()
        if id == "":
            id = self._taskGenerator.newCount()
            task.setId(id)
        self.listTask[id] = task
        self._p_changed=1

    def removeTask(self, task):
        task.delete()
        if task in self.listTask.values():
            del self.listTask[task.getId()]
            self._p_changed=1

    def getTaskById(self, id):
        return self.listTask[id]


class HelperTaskList:
    """Helper class used for getting and instance of taskList.
        It will be migrated into a static method in taskList class once the
        ZODB4 is released and the Persistent classes are no longer Extension
        ones.
    """

    def getTaskListInstance(cls):
        dbmgr = DBMgr.getInstance()
        root = dbmgr.getDBConnection().root()
        try:
            tlist = root["taskList"]["main"]
        except KeyError, e:
            tlist = taskList()
            root["taskList"] = OOBTree.OOBTree()
            root["taskList"]["main"] = tlist
        return tlist

    getTaskListInstance = classmethod( getTaskListInstance )


class task(Persistent):
    """
    keep the time info about a task and a list of object to run when the task is activate
    """
    def __init__(self):
        self.startDate = None
        self.endDate = None
        self.interval = None
        self.lastDate = None
        self.listObj = {}
        self.id = ""
        self._objGenerator = Counter()
        self.owner = None
        self.running = False

    def __cmp__(self, other):
        if type(self) is not type(other):
            # This is actually dangerous and the ZODB manual says not to do this
            # because it relies on memory order. However, this branch should never
            # be taken anyway since we do not store different types in the same set
            # or use them as keys.
            return cmp(hash(self), hash(other))
        return cmp(self.getId(), other.getId())

    def prerun(self):
        """prerun returns False if the prerun was ok and True in case we need to abort the task."""
        return False

    def getOwner(self):
        return self.owner

    def setOwner(self, owner):
        self.owner = owner

    def isRunning(self):
        try:
            if self.running:
                pass
        except AttributeError, e:
            self.running = False
        return self.running

    def setRunning(self, r):
        self.running = r

    def getId(self):
        return self.id

    def setId(self, id):
        self.id = id

    def getTimezone(self):
        if self.owner:
            try:
                return self.owner.getTimezone()
            except:
                return None
        return None

    def setStartDate(self, date):
        self.startDate = date
        self._p_changed=1

    def getStartDate(self):
        return self.startDate

    def getAdjustedStartDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
           tz = 'UTC'
        return self.getStartDate().astimezone(timezone(tz))

    def setEndDate(self, date):
        self.endDate = date
        self._p_changed=1

    def getEndDate(self):
        return self.endDate

    def getAdjustedEndDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
           tz = 'UTC'
        return self.getEndDate().astimezone(timezone(tz))

    def setInterval(self, interval):
        self.interval = interval
        self._p_changed=1

    def getInterval(self):
        return self.interval

    def getObjList(self):
        return self.listObj.values()

    def addObj(self, obj):
        id = obj.getId()
        if id == "":
            id = self._objGenerator.newCount()
            obj.setId(id)
        self.listObj[id] = obj
        self._p_changed=1

    def removeObj(self, obj):
        if obj in self.listObj.values():
            del self.listObj[ obj.getId() ]
            self._p_changed=1

    def getObjById(self, id):
        return self.listObj[id]

    def setLastDate(self, date):
        self.lastDate = date
        self._p_changed=1

    def getLastDate(self):
        return self.lastDate

    def getAdjustedLastDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
           tz = 'UTC'
        if self.getLastDate():
            return self.getLastDate().astimezone(timezone(tz))
        return None

    def delete(self):
        for obj in self.getObjList():
            obj.endTask()

class obj(Persistent):
    """
    interface for object which can be attach to a task
    """

    def __init__(self):
        self.id = ""

    def run(self):
        """
        This method contain the code to do when the object is activated
        """
        pass

    def endTask(self):
        """This method will be called when the task finish"""
        pass

    def getId(self):
        try:
            return self.id
        except:
            self.id = ""
            return self.id

    def setId(self, id):
        self.id = id


class sendMail(obj):
    """
    """
    def __init__(self):
        obj.__init__(self)
        self.fromAddr = ""
        self.toAddr = []
        self.toUser = []
        self.ccAddr = []
        self.subject = ""
        self.text = ""
        self.smtpServer = Config.getInstance().getSmtpServer()

    def run(self):
        addrs = []
        ccaddrs = []
        for addr in self.toAddr:
            addrs.append(smtplib.quoteaddr(addr))
        for ccaddr in self.ccAddr:
            ccaddrs.append(smtplib.quoteaddr(ccaddr))
        for user in self.toUser:
            addrs.append(smtplib.quoteaddr(user.getEmail()))
        maildata = { "fromAddr": self.fromAddr, "toList": addrs, "ccList": ccaddrs, "subject": self.subject, "body": self.text }
        GenericMailer.send(GenericNotification(maildata))

    def setFromAddr(self, addr):
        self.fromAddr = addr
        self._p_changed = 1

    def getFromAddr(self):
        return self.fromAddr

    def initialiseToAddr( self ):
        self.toAddr = []
        self._p_changed=1

    def addToAddr(self, addr):
        if not addr in self.toAddr:
            self.toAddr.append(addr)
            self._p_changed=1

    def addCcAddr(self, addr):
        if not addr in self.ccAddr:
            self.ccAddr.append(addr)
            self._p_changed=1

    def removeToAddr(self, addr):
        if addr in self.toAddr:
            self.toAddr.remove(addr)
            self._p_changed=1

    def setToAddrList(self, addrList):
        """Params: addrList -- addresses of type : list of str."""
        self.toAddr = addrList
        self._p_changed=1

    def getToAddrList(self):
        return self.toAddr

    def setCcAddrList(self, addrList):
        """Params: addrList -- addresses of type : list of str."""
        self.ccAddr = addrList
        self._p_changed=1

    def getCcAddrList(self):
        return self.ccAddr

    def addToUser(self, user):
        if not user in self.toUser:
            self.toUser.append(user)
            self._p_changed=1

    def removeToUser(self, user):
        if user in self.toUser:
            self.toUser.remove(user)
            self._p_changed=1

    def getToUserList(self):
        return self.toUser

    def setSubject(self, subject):
        self.subject = subject

    def getSubject(self):
        return self.subject

    def setText(self, text):
        self.text = text

    def getText(self):
        return self.text

    def delete(self):
        TrashCanManager().add(self)

    def recover(self):
        self.smtpServer = Config.getInstance().getSmtpServer()
        TrashCanManager().remove(self)


class FoundationSync( obj ):
    """
    Synchronizes room data (along with associated room managers
    and equipment) with Foundation database.

    Also, updates list of CERN Official Holidays

    (This is object for a task class)
    """
    def __init__(self):
        obj.__init__(self)

    def run(self):
        from MaKaC.common.FoundationSync.foundationSync import FoundationSync
        FoundationSync().doAll()

    def delete(self):
        TrashCanManager().add( self )

    def recover(self):
        TrashCanManager().remove( self )

    @staticmethod
    def register():
        """
        Run ONCE to add FoundationSync task
        """
        # Connect to Indico DB
        DBMgr.getInstance().startRequest()
        DBMgr.getInstance().sync()
        TASK_ID = 'FoundationSyncTask'

        t = task()
        t.setId( TASK_ID )
        d = nowutc() + timedelta( days = 1 )
        t.setStartDate( d.replace( hour=0, minute=0, second=0, microsecond=0 )) # This midnight
        t.setInterval( timedelta( days = 1 ) )
        t.addObj( FoundationSync() )

        # Check if tasks existis
        taskList = HelperTaskList.getTaskListInstance()
        for existing in taskList.getTasks():
            if existing.getId() == t.getId():
                print TASK_ID + " is already registered"
                return

        # Task does not exist: add it
        taskList.addTask( t )

        # Disconnect from Indico DB
        DBMgr.getInstance().endRequest()
        print "Successfully registered " + TASK_ID


class timer(Thread):
    """
    When thread started, call the function 'func' each 'interval' using the worker class
    """
    def __init__(self, interval, log):
        Thread.__init__(self)
        self._inter = interval
        self.log = log
        self.st = 0

    def stop(self):
        self.st = 1

    def setInterval(self, interval):
        self._inter = interval

    def run(self):
        while not self.st:
            w = worker(self.log)
            w.start()
            time.sleep(self._inter)
        print "thread stopped"


class worker(Thread):
    """
    call the function 'func' in a thread
    """
    def __init__(self, log):
        Thread.__init__(self)
        self.log = log

    def run(self):
        workerFilename = os.path.join(os.path.abspath(os.path.dirname(__file__)), "execProcess.py")
        log=""
        if self.log:
            log="\"%s\""%self.log
        os.system("%s \"%s\" %s"%(sys.executable, workerFilename, log))



class Alarm(task):
    """
    implement an alarm componment
    """
    def __init__(self, conf):
        task.__init__(self)
        self.mail = sendMail()
        self.addObj(self.mail)
        self.conf = conf
        self.timeBefore = None
        self.text = ""
        self.note = ""
        self.confSumary = False
        self.toAllParticipants = False

    def getToAllParticipants(self):
        try:
            return self.toAllParticipants
        except:
            self.toAllParticipants = False
            return self.toAllParticipants

    def setToAllParticipants(self, toAllParticipants):
        self.toAllParticipants = toAllParticipants

    def clone(self, conference):
        alarm = Alarm(conference)
        alarm.initialiseToAddr()
        for addr in self.getToAddrList():
            alarm.addToAddr(addr)
        alarm.setFromAddr(self.getFromAddr())
        alarm.setSubject(self.getSubject())
        alarm.setConfSumary(self.getConfSumary())
        alarm.setNote(self.getNote())
        alarm.setText(self.getText())
        if self.getTimeBefore() is not None:
            alarm.setTimeBefore(copy.copy(self.getTimeBefore()))
        else:
            alarm.setStartDate(copy.copy(self.getStartDate()))
        alarm.setToAllParticipants(self.getToAllParticipants())
        return alarm

    def getStartDate(self):
        if self.timeBefore:
            return self.conf.getStartDate() - self.timeBefore
        else:
            return task.getStartDate(self)

    def getAdjustedStartDate(self,tz=None):
        if not tz:
            tz = self.conf.getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        if self.timeBefore:
            return self.conf.getStartDate().astimezone(timezone(tz)) - self.timeBefore
        else:
            if task.getStartDate(self):
                return task.getStartDate(self).astimezone(timezone(tz))
            return None
        if self.getStartDate():
            return self.getStartDate().astimezone(timezone(tz))
        return None

    def setStartDate(self, date):
        #we don't need timeBefore if startDate is set
        self.startDate = date
        self.timeBefore = None
        self._p_changed=1

    def setTimeBefore(self, timeDelta):
        #we don't need startDate if timeBefore is set
        self.timeBefore = timeDelta
        self.startDate = None
        self._p_changed=1

    def getTimeBefore(self):
        return self.timeBefore

    def setFromAddr(self, addr):
        self.mail.setFromAddr(addr)

    def getFromAddr(self):
        return self.mail.getFromAddr()

    def initialiseToAddr(self):
        self.mail.initialiseToAddr()

    def addToAddr(self, addr):
        self.mail.addToAddr(addr)

    def addCcAddr(self, addr):
        self.mail.addCcAddr(addr)

    def removeToAddr(self, addr):
        self.mail.removeToAddr(addr)

    def setToAddrList(self, addrList):
        self.mail.setToAddrList(addrList)

    def getToAddrList(self):
        return self.mail.getToAddrList()

    def setCcAddrList(self, addrList):
        self.mail.setCcAddrList(addrList)

    def getCcAddrList(self):
        return self.mail.getCcAddrList()

    def addToUser(self, user):
        self.mail.addToUser(user)
        if isinstance(user, Avatar):
            user.linkTo(self, "to")

    def removeToUser(self, user):
        self.mail.removeToUser(user)
        if isinstance(user, Avatar):
            user.unlinkTo(self, "to")

    def getToUserList(self):
        return self.mail.getToUserList()

    def setSubject(self, subject):
        self.mail.setSubject(subject)

    def getSubject(self):
        return self.mail.getSubject()

    def setText(self, text):
        self.text = text
        self._setMailText()
        self._p_changed=1

    def getText(self):
        return self.text

    def getLocator(self):
        d = self.getOwner().getLocator()
        d["alarmId"] = self.getId()
        return d

    def canAccess(self, aw):
        return self.getOwner().canAccess(aw)

    def canModify(self, aw):
        return self.getOwner().canModify(aw)

    def _setMailText(self):
        text = self.text
        if self.note:
            text = text + "Note: %s" % self.note
        if self.confSumary:
            #try:
                from MaKaC.common.output import outputGenerator
                from MaKaC.accessControl import AdminList, AccessWrapper
                import MaKaC.webinterface.urlHandlers as urlHandlers
                admin = AdminList().getInstance().getList()[0]
                aw = AccessWrapper()
                aw.setUser(admin)
                path = Config.getInstance().getStylesheetsDir()
                if os.path.exists("%s/text.xsl" % path):
                    stylepath = "%s/text.xsl" % path
                outGen = outputGenerator(aw)
                vars = { \
                        "modifyURL": urlHandlers.UHConferenceModification.getURL( self.conf ), \
                        "sessionModifyURLGen": urlHandlers.UHSessionModification.getURL, \
                        "contribModifyURLGen": urlHandlers.UHContributionModification.getURL, \
                        "subContribModifyURLGen":  urlHandlers.UHSubContribModification.getURL, \
                        "materialURLGen": urlHandlers.UHMaterialDisplay.getURL, \
                        "resourceURLGen": urlHandlers.UHFileAccess.getURL }
                confText = outGen.getOutput(self.conf,stylepath,vars)
                text += "\n\n\n" + confText
            #except:
            #    text += "\n\n\nSorry could not embed text version of the agenda..."
        self.mail.setText(text)

    def setNote(self, note):
        self.note = note
        self._setMailText()
        self._p_changed=1

    def getNote(self):
        return self.note

    def setConfSumary(self, val):
        self.confSumary = val
        self._setMailText()
        self._p_changed=1

    def getConfSumary(self):
        return self.confSumary

    def prerun(self):
        # Date checkings...
        from MaKaC.conference import ConferenceHolder
        if not ConferenceHolder().hasKey(self.conf.getId()) or \
                self.conf.getStartDate() <= nowutc():
            self.conf.removeAlarm(self)
            return True
        # Email
        self.setSubject("Event reminder: %s"%self.conf.getTitle())
        try:
            locationText = self.conf.getLocation().getName()
            if self.conf.getLocation().getAddress() != "":
                locationText += ", %s" % self.conf.getLocation().getAddress()
            if self.conf.getRoom().getName() != "":
                locationText += " (%s)" % self.conf.getRoom().getName()
        except:
            locationText = ""
        if locationText != "":
            locationText = i18nformat(""" _("Location"): %s""") % locationText

        if self.getToAllParticipants() :
            for p in self.conf.getParticipation().getParticipantList():
                self.addToUser(p)

        from MaKaC.webinterface import urlHandlers
        if Config.getInstance().getShortEventURL() != "":
            url = "%s%s" % (Config.getInstance().getShortEventURL(),self.conf.getId())
        else:
            url = urlHandlers.UHConferenceDisplay.getURL( self.conf )
        self.setText("""Hello,
    Please note that the event "%s" will start on %s (%s).
    %s

    You can access the full event here:
    %s

Best Regards

    """%(self.conf.getTitle(),\
                self.conf.getAdjustedStartDate().strftime("%A %d %b %Y at %H:%M"),\
                self.conf.getTimezone(),\
                locationText,\
                url,\
                ))
        self._setMailText()
        return False

    def delete(self):
        for obj in self.getObjList():
            self.removeObj(obj)
            # Id the delete method doesn't exist for obj it has to be
            # implemented.
            obj.delete()
        #self.conf = None
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

class StatisticsUpdater(obj):
    def __init__(self, cat):
        self._cat = cat

    def run( self ):
        CategoryStatistics.updateStatistics(self._cat)

    def delete(self):
        for obj in self.getObjList():
            self.removeObj(obj)
            # Id the delete method doesn't exist for obj it has to be
            # implemented.
            obj.delete()
        self.conf = None
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

if __name__ == "__main__":
    """
    run the function listed in the toExec instance each hours
    """
    duration = 3600
    te = toExec()
    t = timer(duration, te.execute)
    t.start()
