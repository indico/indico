# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import copy, logging, os, time
from dateutil import rrule
from datetime import timedelta
import zope.interface

# Required by specific tasks
from MaKaC.user import Avatar
from MaKaC.i18n import _
from MaKaC.common import Config
# end required

from persistent import Persistent
from BTrees.IOBTree import IOBTree

from indico.util.fossilize import fossilizes, Fossilizable
from indico.util.date_time import int_timestamp
from indico.modules.scheduler.fossils import ITaskFossil, ITaskOccurrenceFossil
from indico.modules.scheduler import base
from indico.core.index import IUniqueIdProvider, IIndexableByArbitraryDateTime

"""
Defines base classes for tasks, and some specific tasks as well
"""


class TimedEvent(Persistent, Fossilizable):

    zope.interface.implements(IUniqueIdProvider,
                              IIndexableByArbitraryDateTime)

    def getIndexingDateTime(self):
        return int_timestamp(self._getCurrentDateTime())

    def _getCurrentDateTime(self):
        # just get current date/time
        return base.TimeSource.get().getCurrentTime()

    def __conform__(self, proto):

        if proto == IIndexableByArbitraryDateTime:
            return self.getIndexingDateTime()
        else:
            return None


class BaseTask(TimedEvent):
    """
    A base class for tasks.
    `expiryDate` is the last point in time when the task can run. A task will
    refuse to run if current time is past `expiryDate`
    """

    fossilizes(ITaskFossil)

    def __init__(self, expiryDate=None):
        self.createdOn = self._getCurrentDateTime()
        self.expiryDate = expiryDate
        self.typeId = self.__class__.__name__
        self.id = None
        self.reset()
        self.status = 0

        self.startedOn = None
        self.endedOn = None

    def reset(self):
        '''Resets a task to its state before being run'''

        self.running = False
        self.onRunningListSince = None

    # Time methods

    def getCreatedOn(self):
        return self.createdOn

    def getEndedOn(self):
        return self.endedOn

    def setEndedOn(self, dateTime):
        self.endedOn = dateTime

    def getStartedOn(self):
        return self.startedOn

    def setOnRunningListSince(self, sometime):
        self.onRunningListSince = sometime
        self._p_changed = 1

    def getOnRunningListSince(self):
        return self.onRunningListSince

    def setStatus(self, newstatus):
        self.getLogger().info("%s set status %s" % (self, base.status(newstatus)))
        self.status = newstatus

    def getStatus(self):
        return self.status

    def getId(self):
        return self.id

    def getUniqueId(self):
        return "task%s" % self.id

    def getTypeId(self):
        return self.typeId

    def initialize(self, newid, newstatus):
        self.id = newid
        self.setStatus(newstatus)

    def plugLogger(self, logger):
        self._v_logger = logger

    def getLogger(self):
        if not hasattr(self, '_v_logger') or not self._v_logger:
            self._v_logger = logging.getLogger('task/%s' % self.typeId)
        return self._v_logger

    def prepare(self):
        """
        This information will be saved regardless of the task being repeated or not
        """

        curTime = self._getCurrentDateTime()
        tsDiff = int_timestamp(curTime) - int_timestamp(self.getStartOn())

        if tsDiff < 0:
            self.getLogger().debug('Task %s will wait for some time. (%s) > (%s)' % \
                                   (self.id, self.getStartOn(), curTime))
            base.TimeSource.get().sleep(tsDiff)

        if self.expiryDate and curTime > self.expiryDate:
            self.getLogger().warning(
                'Task %s will not be executed, expiryDate (%s) < current time (%s)' % \
                (self.id, self.expiryDate, curTime))
            return False

        self.startedOn = curTime
        self.running = True
        self.setStatus(base.TASK_STATUS_RUNNING)

    def start(self):

        try:
            self.run()
        finally:
            self.running = False
            self.endedOn = self._getCurrentDateTime()

    def tearDown(self):
        """
        If a task needs to do something once it has run and been removed
        from runningList, overload this method
        """
        pass

    def __str__(self):
        return "[%s:%s|%s]" % (self.typeId, self.id,
                               base.status(self.status))


class OneShotTask(BaseTask):
    """
    Tasks that are executed only once
    """

    def __init__(self, startDateTime, expiryDate = None):
        super(OneShotTask, self).__init__(expiryDate = expiryDate)
        self.startDateTime = startDateTime

    def getStartOn(self):
        return self.startDateTime

    def setStartOn(self, newtime):
        self.startDateTime = newtime

    def suicide(self):
        self.setStatus(base.TASK_STATUS_TERMINATED)
        self.setEndedOn(self._getCurrentDateTime())


class PeriodicTask(BaseTask):
    """
    Tasks that should be executed at regular intervals
    """

    def __init__(self, frequency, **kwargs):
        """
        :param frequency: a valid dateutil frequency specifier (DAILY, HOURLY, etc...)
        """
        super(PeriodicTask, self).__init__()

        self._nextOccurrence = None
        self._lastFinishedOn = None
        self._occurrences = IOBTree()
        self._occurrenceCount = 0
        self._repeat = True

        if 'dtstart' not in kwargs:
            kwargs['dtstart'] = self._getCurrentDateTime()

        self._rule = rrule.rrule(
            frequency,
            **kwargs
            )

        self._nextOccurrence = self._rule.after(
            kwargs['dtstart'] - timedelta(seconds=1),
            inc = True)



    def start(self):
        super(PeriodicTask, self).start()

    def tearDown(self):
        super(PeriodicTask, self).tearDown()

    def setNextOccurrence(self, dateAfter = None):

        if not self._nextOccurrence:
            # if it's None already, it means there's no "future"
            return

        if not dateAfter:
            dateAfter = self._getCurrentDateTime()

        # find next date after
        nextOcc = self._rule.after(max(self._nextOccurrence, dateAfter),
                                   inc = False)

        # repeat process till a satisfactory date is found
        # or there is nothing left to check
        #while nextOcc and nextOcc < dateAfter:
        #    nextOcc = self._rule.after(nextOcc,
        #                               inc = False)

        self._nextOccurrence = nextOcc
        return nextOcc

    def getStartOn(self):
        return self._nextOccurrence

    def getLastFinishedOn(self):
        return self._lastFinishedOn

    def addOccurrence(self, occurrence):
        occurrence.setId(self._occurrenceCount)
        self._occurrences[self._occurrenceCount] = occurrence
        self._occurrenceCount += 1

    def dontComeBack(self):
        self._repeat = False

    def shouldComeBack(self):
        return self._repeat


class PeriodicUniqueTask(PeriodicTask):
    """
    Singleton periodic tasks: no two or more PeriodicUniqueTask of this
    class will be queued or running at the same time (TODO)
    """
    # TODO: implement this


class TaskOccurrence(TimedEvent):
    """
    Wraps around a PeriodicTask object, and represents an occurrence of this task
    """

    fossilizes(ITaskOccurrenceFossil)


    def __init__(self, task):
        self._task = task
        self._startedOn = task.getStartedOn()
        self._endedOn = task.getEndedOn()
        self._id = None

    def getId(self):
        return self._id

    def getUniqueId(self):
        return "%s:%s" % (self._task.getUniqueId(), self._id)

    def setId(self, occId):
        self._id = occId

    def getStartedOn(self):
        return self._startedOn

    def getEndedOn(self):
        return self._endedOn

    def getTask(self):
        return self._task


class CategoryStatisticsUpdaterTask(PeriodicUniqueTask):
    '''Updates statistics associated with categories
    '''
    def __init__(self, cat, frequency, **kwargs):
        super(CategoryStatisticsUpdaterTask, self).__init__(frequency,
                                                            **kwargs)
        self._cat = cat

    def run(self):
        from MaKaC.statistics import CategoryStatistics
        CategoryStatistics.updateStatistics(self._cat,
                                            self.getLogger())


# TODO: Isolate CERN Specific
class FoundationSyncTask(PeriodicUniqueTask):
    """
    Synchronizes room data (along with associated room managers
    and equipment) with Foundation database.

    Also, updates list of CERN Official Holidays

    (This is object for a task class)
    """
    def __init__(self, frequency, **kwargs):
        super(FoundationSyncTask, self).__init__(frequency, **kwargs)

    def run(self):
        from MaKaC.common.FoundationSync.foundationSync import FoundationSync
        FoundationSync(self.getLogger()).doAll()


class SendMailTask(OneShotTask):
    """
    """
    def __init__(self, startDateTime):
        super(SendMailTask, self).__init__(startDateTime)
        self.fromAddr = ""
        self.toAddr = []
        self.toUser = []
        self.ccAddr = []
        self.subject = ""
        self.text = ""
        self.smtpServer = Config.getInstance().getSmtpServer()

    def _prepare(self, check):
        """
        Overloaded by descendants
        """

    def run(self, check=True):
        import smtplib
        from MaKaC.webinterface.mail import GenericMailer, GenericNotification

        # prepare the mail
        send = self._prepare(check=check)

        # _prepare decided we shouldn't send the mail?
        if not send:
            return

        addrs = [smtplib.quoteaddr(x) for x in self.toAddr]
        ccaddrs = [smtplib.quoteaddr(x) for x in self.ccAddr]

        if len(addrs) + len(ccaddrs) == 0:
            self.getLogger().warning("Attention: mail contains no recipients!")
        else:
            self.getLogger().info("Sending mail To: %s, CC: %s" % (addrs, ccaddrs))

        for user in self.toUser:
            addrs.append(smtplib.quoteaddr(user.getEmail()))

        GenericMailer.send(GenericNotification({"fromAddr": self.fromAddr,
                                                "toList": addrs,
                                                "ccList": ccaddrs,
                                                "subject": self.subject,
                                                "body": self.text }))

    def setFromAddr(self, addr):
        self.fromAddr = addr
        self._p_changed = 1

    def getFromAddr(self):
        return self.fromAddr

    def addToAddr(self, addr):
        if not addr in self.toAddr:
            self.toAddr.append(addr)
            self._p_changed = 1

    def addCcAddr(self, addr):
        if not addr in self.ccAddr:
            self.ccAddr.append(addr)
            self._p_changed = 1

    def removeToAddr(self, addr):
        if addr in self.toAddr:
            self.toAddr.remove(addr)
            self._p_changed = 1

    def setToAddrList(self, addrList):
        """Params: addrList -- addresses of type : list of str."""
        self.toAddr = addrList
        self._p_changed = 1

    def getToAddrList(self):
        return self.toAddr

    def setCcAddrList(self, addrList):
        """Params: addrList -- addresses of type : list of str."""
        self.ccAddr = addrList
        self._p_changed = 1

    def getCcAddrList(self):
        return self.ccAddr

    def addToUser(self, user):
        if not user in self.toUser:
            self.toUser.append(user)
            self._p_changed = 1

    def removeToUser(self, user):
        if user in self.toUser:
            self.toUser.remove(user)
            self._p_changed = 1

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


class AlarmTask(SendMailTask):
    """
    implement an alarm componment
    """
    def __init__(self, conf, confRelId, startDateTime=None, relative=None):

        self.conf = conf
        super(AlarmTask, self).__init__(startDateTime)

        if not startDateTime:
            startDateTime = self.conf.getStartDate() - relative

        self.setRelative(relative)
        self.setStartOn(startDateTime)

        self.text = ""
        self.note = ""
        self.confSumary = False
        self.toAllParticipants = False
        self._confRelId = confRelId
        self._relative = relative

    def getConference(self):
        return self.conf

    def getConfRelativeId(self):
        return self._confRelId

    def getToAllParticipants(self):
        try:
            return self.toAllParticipants
        except:
            self.toAllParticipants = False
            return self.toAllParticipants

    def setRelative(self, relative):
        self._relative = relative

    def setToAllParticipants(self, toAllParticipants):
        self.toAllParticipants = toAllParticipants

    def clone(self, conference):
        """
        Clone the alarm, changing only the conference
        """
        alarm = conference.newAlarm(self._relative or self.getStartOn())
        for addr in self.getToAddrList():
            alarm.addToAddr(addr)
        alarm.setFromAddr(self.getFromAddr())
        alarm.setSubject(self.getSubject())
        alarm.setConfSummary(self.getConfSummary())
        alarm.setNote(self.getNote())
        alarm.setText(self.getText())
        alarm.setToAllParticipants(self.getToAllParticipants())
        return alarm

    def getTimeBefore(self):
        # TODO: remove this
        if not hasattr(self, '_relative'):
            self._relative = None
        return self._relative

    def addToUser(self, user):
        super(AlarmTask, self).addToUser(user)
        if isinstance(user, Avatar):
            user.linkTo(self, "to")

    def removeToUser(self, user):
        super(AlarmTask, self).removeToUser(user)
        if isinstance(user, Avatar):
            user.unlinkTo(self, "to")

    def getText(self):
        return self.text

    def getLocator(self):
        d = self.conf.getLocator()
        d["alarmId"] = self.getConfRelativeId()
        return d

    def canAccess(self, aw):
        return self.conf.canAccess(aw)

    def canModify(self, aw):
        return self.conf.canModify(aw)

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
        super(AlarmTask, self).setText(text)

    def setNote(self, note):
        self.note = note
        self._setMailText()
        self._p_changed=1

    def getNote(self):
        return self.note

    def setConfSummary(self, val):
        self.confSumary = val
        self._setMailText()
        self._p_changed=1

    def getConfSummary(self):
        return self.confSumary

    def _prepare(self, check = True):

        # Date checks...
        if check:
            from MaKaC.conference import ConferenceHolder
            if not ConferenceHolder().hasKey(self.conf.getId()):
                self.getLogger().warning("Conference %s no longer exists! "
                                     "Deleting alarm." % self.conf.getId())
                self.conf.removeAlarm(self)
                self.suicide()
            elif self.conf.getStartDate() <= self._getCurrentDateTime():
                self.getLogger().warning("Conference %s already started. "
                                     "Deleting alarm." % self.conf.getId())
                self.conf.removeAlarm(self)
                self.suicide()
                return False

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
            locationText = _(""" _("Location"): %s""") % locationText

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
        return True


class SampleOneShotTask(OneShotTask):
    def run(self):
        self.getLogger().debug('Now i shall sleeeeeeeep!')
        base.TimeSource.get().sleep(1)
        self.getLogger().debug('%s executed' % self.__class__.__name__)


class SamplePeriodicTask(PeriodicTask):
    def run(self):
        base.TimeSource.get().sleep(1)
        self.getLogger().debug('%s executed' % self.__class__.__name__)
