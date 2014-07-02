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

import logging
import urllib

import zope.interface
from persistent import Persistent
from flask import render_template

from MaKaC.user import Avatar
from MaKaC.authentication.LDAPAuthentication import LDAPConnector

from indico.util.fossilize import fossilizes, Fossilizable
from indico.util.date_time import int_timestamp, format_datetime
from indico.modules.scheduler.fossils import ITaskFossil
from indico.modules.scheduler import base
from indico.core.index import IUniqueIdProvider, IIndexableByArbitraryDateTime
from indico.core.config import Config


# Defines base classes for tasks, and some specific tasks as well


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

    # seconds to consider a task AWOL
    _AWOLThresold = 6000

    def __init__(self, expiryDate=None):
        self.createdOn = self._getCurrentDateTime()
        self.expiryDate = expiryDate
        self.typeId = self.__class__.__name__
        self.id = None
        self.reset()
        self.status = 0

        self.startedOn = None
        self.endedOn = None

    def __cmp__(self, obj):
        from indico.modules.scheduler.tasks.periodic import TaskOccurrence
        if obj is None:
            return 1
        elif isinstance(obj, TaskOccurrence):
            task_cmp = cmp(self, obj.getTask())
            if task_cmp == 0:
                return -1
            else:
                return task_cmp
        # This condition will mostlike never happen
        elif not isinstance(obj, BaseTask) or (self.id == obj.id and self.id is None):
            return cmp(hash(self), hash(obj))
        # This is the 'default case' where we are comparing 2 Tasks
        else:
            return cmp(self.id, obj.id)

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

    def setStartedOn(self, dateTime):
        self.startedOn = dateTime

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
        tsDiff = int_timestamp(self.getStartOn()) - int_timestamp(curTime)

        if tsDiff > 0:
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

    def start(self, delay):
        self._executionDelay = delay
        try:
            self.run()
            self.endedOn = self._getCurrentDateTime()
        finally:
            LDAPConnector.destroy()
            self.running = False

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

        # just in case some ill-behaved code generates empty addresses
        addrs = list(smtplib.quoteaddr(x) for x in self.toAddr if x)
        ccaddrs = list(smtplib.quoteaddr(x) for x in self.ccAddr if x)

        if len(addrs) + len(ccaddrs) == 0:
            self.getLogger().warning("Attention: no recipients, mail won't be sent")
        else:
            self.getLogger().info("Sending mail To: %s, CC: %s" % (addrs, ccaddrs))

        for user in self.toUser:
            addrs.append(smtplib.quoteaddr(user.getEmail()))

        if addrs or ccaddrs:
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
        alarm = conference.newAlarm(self.getTimeBefore() or self.getStartOn())
        for addr in self.getToAddrList():
            alarm.addToAddr(addr)
        alarm.setFromAddr(self.getFromAddr())
        alarm.setUpSubject()
        alarm.setConfSummary(self.getConfSummary())
        alarm.setNote(self.getNote())
        alarm.setText(self.getText())
        alarm.setToAllParticipants(self.getToAllParticipants())
        return alarm

    def delete(self):
        self.getConference().removeAlarm(self)

    def getTimeBefore(self):
        # TODO: remove this
        if not hasattr(self, '_relative'):
            self._relative = None
        return self._relative

    def setUpSubject(self):
        startDateTime = format_datetime(self.conf.getAdjustedStartDate(), format="short")
        self.setSubject(_("Event reminder: %s (%s %s)") % (self.conf.getTitle(), startDateTime, self.conf.getTimezone()))

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

    def setNote(self, note):
        self.note = note
        self._p_changed=1

    def getNote(self):
        return self.note

    def setConfSummary(self, val):
        self.confSumary = val
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
        self.setUpSubject()
        if self.getToAllParticipants() :
            if self.conf.getType() == "conference":
                for r in self.conf.getRegistrantsList():
                    self.addToUser(r)
            else:
                for p in self.conf.getParticipation().getParticipantList() :
                    self.addToUser(p)

        from MaKaC.webinterface import urlHandlers
        if Config.getInstance().getShortEventURL() != "":
            url = "%s%s" % (Config.getInstance().getShortEventURL(),self.conf.getId())
        else:
            url = urlHandlers.UHConferenceDisplay.getURL(self.conf)

        self.setText(render_template('alarm_email.txt',
            event=self.conf.fossilize(),
            url=url,
            note=self.note,
            with_agenda=self.confSumary,
            agenda=[e.fossilize() for e in self.conf.getSchedule().getEntries()]
        ))

        return True


class HTTPTask(OneShotTask):
    def __init__(self, url, data=None):
        super(HTTPTask, self).__init__(base.TimeSource.get().getCurrentTime())
        self._url = url
        self._data = data

    def run(self):
        method = 'POST' if self._data is not None else 'GET'
        self.getLogger().info('Executing HTTP task: %s %s' % (method, self._url))
        data = urllib.urlencode(self._data) if self._data is not None else None
        req = urllib.urlopen(self._url, data)
        req.close()


class SampleOneShotTask(OneShotTask):
    def run(self):
        self.getLogger().debug('Now i shall sleeeeeeeep!')
        base.TimeSource.get().sleep(1)
        self.getLogger().debug('%s executed' % self.__class__.__name__)
