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

from datetime import datetime, timedelta
import MaKaC.common.indexes as indexes
from indico.core.db import DBMgr
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.mail import GenericNotification
from MaKaC.common.info import HelperMaKaCInfo
from indico.modules.scheduler import Scheduler
from indico.modules.scheduler.tasks import OneShotTask
from persistent import Persistent
from MaKaC.user import AvatarHolder
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.i18n import _
from indico.core.config import Config
from MaKaC.common import mail
###---------------------------- General Pending Queues ---------------------------------

#---GENERAL----

class PendingHolder(object):
    """ This is an index that holds all the requests to add pending people to become
        Indico users.
        Those participants are not Avatars yet (do not have Indico account) and that's why
        they are in this pending queue. So once they become Indico users they will be removed
        from the index"""

    def __init__(self):
        """Index by email of all the request and all the tasks with the reminders"""
        self._id=""
        self._idx = None # All the pendign users
        self._tasksIdx=None # Tasks which send reminder emails periodically asking for the creation of one indico account
        self._reminder=PendingReminder

    def getPendingByEmail(self, email):
        return self._idx.matchPendingUser(email)

    def removePending(self, sb):
        """Remove the pendant from the queue, and if it's the last one then remove the task"""
        self._idx.unindexPendingUser(sb)
        email=sb.getEmail().lower().strip()
        if self.getPendingByEmail(email)==[]:
            self._removeTask(email)

    def addPending(self, sb, sendEmail=True, sendPeriodicEmail=False):
        """Add a new user to the index, and a new task only the first time"""
        self._idx.indexPendingUser(sb)
        email=sb.getEmail().lower().strip()
        sendEmail=sendEmail and not self._hasTask(email)
        if sendEmail:
            self._sendReminderEmail(sb)
        if sendPeriodicEmail:
            self._addTask(email)

    def grantRights(self, av):
        """We must implement this method in order to grant the specific rights to the new user"""
        pass

    def _sendReminderEmail(self, sb):
        """We must implement this method in order to sent an email with the reminder for the specific pending users"""
        pass


    def _getTasksIdx(self):
        return self._tasksIdx

    def _addTask(self, email):
        """Creating a task in order to send reminder emails periodically.
           It's mandatory to implement this method for the specific pending queues"""
        # ------ Creating a task in order to send reminder emails periodically ------
        if not self._hasTask(email):
            # Create the object which send the email
            pedingReminder = self._reminder(email)
            pedingReminder.setId("ReminderPending%s-%s" % (self._id,email))
            # Create the task
            t=task()
            t.addObj(pedingReminder)
            t.setInterval(timedelta(7)) # Remind each 7 days
            nw=nowutc()
            t.setLastDate(nw) # start in 7 days cos the first email was already sent
            t.setEndDate(nw+timedelta(15)) # keep trying during 15 days
            self._tasksIdx.indexTask(email, t)

            Scheduler.addTask(t)


    def _removeTask(self, email):
        if self._hasTask(email):
            t=self._getTasksIdx().matchTask(email)[0]
            Scheduler.removeTask(t)
            self._tasksIdx.unindexTask(email, t)

    def _hasTask(self, email):
        return self._getTasksIdx().matchTask(email) != []


class _PendingNotification(GenericNotification):

    def __init__(self, psList):
        self._psList = psList
        self._participationsByConf = self._calculateParticipationsByConf()
        self._forceIndicoFromAddress = len(self._participationsByConf) > 1
        data = {}
        data["subject"] = "[Indico] User account creation required"
        data["toList"] = [self._psList[0].getEmail()]
        GenericNotification.__init__(self, data)

    def getFromAddr(self):
        # TODO: There will be on "from address" from a conference, but what if there are more different conferences
        supEmail = self._psList[0].getConference().getSupportInfo().getEmail(returnNoReply=True)
        if self._forceIndicoFromAddress or supEmail.strip() == "":
            info = HelperMaKaCInfo.getMaKaCInfoInstance()
            return "%s <%s>".format(info.getTitle(), Config.getInstance().getSupportEmail())
        return supEmail

    def getBody(self):
        # We must implement the body of the email depending of the type of queue
        pass

    def _calculateParticipationsByConf(self):
        d = {}
        for ps in self._psList:
            conf = ps.getConference()
            if conf in d:
                d[conf].append(ps)
            else:
                d[conf] = [ps]
        return d


class PendingReminder(OneShotTask):
    def __init__(self, email, **kwargs):
        super(PendingReminder, self).__init__(**kwargs)
        self._email = email

    def run(self):
        """Mandatory to implement for the specific queues.
           It runs the task of sending an email to the users in order to
           ask them for the creation of the account.

           It returns:
               - TRUE if the pending user has already created the account.
               - FALSE if not."""
        ah = AvatarHolder()
        results=ah.match({"email":self._email}, exact=1)
        av=None
        for i in results:
            if i.getEmail().lower().strip()==self._email.lower().strip():
                av=i
                break
        if av is not None and av.isActivated():
            ph=PendingQueuesHolder()
            ph.grantRights(av)
            return True
        return False

    def tearDown(self):
        '''Inheriting classes must implement this method'''
        raise Exception('Unimplemented tearDown')


    def getEmail(self):
        return self._email
#---END GENERAL


#---SUBMITTERS----

class PendingConfSubmittersHolder(PendingHolder):

    """ This is an index that holds all the requests to add Chairpersons or Speakers in the
        list of avatars with rights to submit material.
        Those participants are not Avatars yet (do not have Indico account) and that's why
        they are in this pending queue. So once they become Indico users they will be removed
        from the index"""

    def __init__(self):
        """Index by email of all the request to add Chairpersons or Speakers"""
        self._id="ConfSubmitters"
        self._idx = indexes.IndexesHolder().getById("pendingConfSubmitters") # All the Conference Chairpersons/Speakers
        self._tasksIdx=indexes.IndexesHolder().getById("pendingConfSubmittersTasks") # Tasks which send reminder emails periodically asking for the creation of one indico account
        self._reminder=PendingConfSubmitterReminder

    def grantRights(self, av):
        l = self.getPendingByEmail(av.getEmail())
        for e in l:
            # We must grant the new avatar with submission rights
            conf = e.getConference()
            conf.getAccessController().grantSubmission(av)

            # the Conference method "removePendingConfSubmitter" will remove the Submitter
            # objects from the conference pending submitter
            # list and from the this index (PendingConfSubmitterHolder).
            e.getConference().getPendingQueuesMgr().removePendingConfSubmitter(e)

    def _sendReminderEmail(self, sb):
        if type(sb)==list:
            notif = _PendingConfSubmitterNotification( sb )
            mail.GenericMailer.send( notif )
        else:
            psList = self.getPendingByEmail(sb.getEmail())
            if psList:
                notif = _PendingConfSubmitterNotification( psList )
                mail.GenericMailer.send( notif )

class _PendingConfSubmitterNotification(_PendingNotification):

    def getBody( self ):
        url = urlHandlers.UHUserCreation.getURL()
        url.addParam("cpEmail",self._psList[0].getEmail())
        return """
    You have been granted with file submission rights for the following event:%s
    Please create an account in Indico in order to use these rights. You can create your account at the following URL:

    <%s>

    *Note that you must use this email address %s when creating the account*

    Best Regards.

    --
    Indico"""%( self._getParticipations(), url, self._psList[0].getEmail() )

    def _getParticipations(self):
        participations = "\n\n"
        for conf in self._participationsByConf.keys():
            participations += """\t\t\t- "Event" \"%s\":\n""" % conf.getTitle()
            accessURL = urlHandlers.UHConferenceDisplay.getURL(conf)
            participations += "\t\t\t\t - Access: %s\n" % accessURL
        return participations


class PendingConfSubmitterReminder(PendingReminder):

    def run(self):
        if not PendingReminder.run(self):
            psl = PendingConfSubmittersHolder().getPendingByEmail(self._email)
            if psl:
                mail.GenericMailer.send(_PendingConfSubmitterNotification(psl))

    def tearDown(self):
        for submitter in PendingConfSubmittersHolder().getPendingByEmail(self._email):
            submitter.getConference().getPendingQueuesMgr().removePendingConfSubmitter(submitter)

    def getPendings(self):
        try:
            return PendingConfSubmittersHolder().getPendingByEmail(self._email)
        except:
            return None

class PendingSubmittersHolder(PendingHolder):

    """ This is an index that holds all the requests to add Authors and Speakers in the
        list of avatars with rights to submit material.
        Those participants are not Avatars yet (do not have Indico account) and that's why
        they are in this pending queue. So once they become Indico users they will be removed
        from the index"""

    def __init__(self):
        """Index by email of all the request to add Authors or Speakers"""
        self._id="Submitters"
        self._idx = indexes.IndexesHolder().getById("pendingSubmitters") # All the ContributionParticipants
        self._tasksIdx=indexes.IndexesHolder().getById("pendingSubmittersTasks") # Tasks which send reminder emails periodically asking for the creation of one indico account
        self._reminder=PendingSubmitterReminder

    def grantRights(self, av):
        l = self.getPendingByEmail(av.getEmail())
        for e in l:
            # We must grant the new avatar with submission rights
            contrib = e.getContribution()
            contrib.grantSubmission(av)

            for email in av.getEmails():
                contrib.revokeSubmissionEmail(email.lower())

            # the Conference method "removePendingSubmitter" will remove the Submitter
            # (type-ContributionParticipation) objects from the conference pending submitter
            # list and from the this index (PendingSubmitterHolder).
            e.getConference().getPendingQueuesMgr().removePendingSubmitter(e)

    def _sendReminderEmail(self, sb):
        from MaKaC.conference import ContributionParticipation
        if type(sb)==list:
            # Sending email just about the contribution participations of the list "sb" (normally
            # they are contributions from one event)
            notif = _PendingSubmitterNotification( sb )
            mail.GenericMailer.send( notif )
        elif isinstance(sb, ContributionParticipation):
            # The param "sb" is a ContributionParticipant, so we send an email with the info
            # about all its participations
            psList=self.getPendingByEmail(sb.getEmail())
            if psList != [] and psList is not None:
                notif = _PendingSubmitterNotification( psList )
                mail.GenericMailer.send( notif )


class _PendingSubmitterNotification(_PendingNotification):

    def getBody( self ):
        url = urlHandlers.UHUserCreation.getURL()
        url.addParam("cpEmail",self._psList[0].getEmail())
        return """
    You have been added as author/speaker of the following contributions:%s
    and material submission rights have been granted to you.
    Please create an account in Indico in order to use these rights. You can create your account at the following URL:

    <%s>

    *Note that you must use this email address %s when creating the account*

    Best Regards.

    --
    Indico"""%( self._getParticipations(), url, self._psList[0].getEmail() )

    def _getParticipations(self):
        participations="\n\n"
        for conf in self._participationsByConf.keys():
            participations+="""\t\t\t- "Event" \"%s\":\n"""%conf.getTitle()
            for ps in self._participationsByConf[conf]:
                contrib=ps.getContribution()
                typeAuthor=""
                if contrib.isPrimaryAuthor(ps):
                    typeAuthor="Primary Author"
                elif contrib.isCoAuthor(ps):
                    typeAuthor="Co-author"
                elif contrib.isSpeaker(ps):
                    typeAuthor="Speaker"
                participations+="""\t\t\t\t - "Contribution" \"%s\" (%s)\n"""%(contrib.getTitle(), typeAuthor)
                accessURL = urlHandlers.UHContributionDisplay.getURL(contrib)
                participations+="\t\t\t\t - Access: %s\n" % accessURL
        return participations

class PendingSubmitterReminder(PendingReminder):

    def run(self):
        hasAccount=PendingReminder.run(self)
        if not hasAccount:
            psh=PendingSubmittersHolder()
            psl=psh.getPendingByEmail(self._email)
            if psl != [] and psl is not None:
                notif = _PendingSubmitterNotification( psl )
                mail.GenericMailer.send( notif )

    def tearDown(self):
        psh=PendingSubmittersHolder()
        psl=psh.getPendingByEmail(self._email)
        for e in psl:
            e.getConference().getPendingQueuesMgr().removePendingSubmitter(e)

    def getPendings(self):
        psh=PendingSubmittersHolder()
        try:
            return psh.getPendingByEmail(self._email)
        except:
            return None

#---END SUBMITTERS

#---PENDING SESSION MANAGERS
class PendingManagersHolder(PendingHolder):

    """ This is an index that holds all the requests to add non existing users in the
        list of avatars with rights to manage.
        Those participants are not Avatars yet (do not have Indico account) and that's why
        they are in this pending queue. So once they become Indico users they will be removed
        from the index"""

    def __init__(self):
        """Index by email of all the requests"""
        self._id="Managers"
        self._idx = indexes.IndexesHolder().getById("pendingManagers") # All the pending managers
        self._tasksIdx=indexes.IndexesHolder().getById("pendingManagersTasks") # Tasks which send reminder emails periodically asking
                                                                               # for the creation of one indico account
        self._reminder=PendingManagerReminder

    def grantRights(self, av):
        l=self.getPendingByEmail(av.getEmail())
        for e in l:
            # We must grant the new avatar with submission rights
            session=e.getSession()
            session.grantModification(av)
            # the ConfPendingQueuesMgr method "removePendingManager" will remove the Manager
            # (type-SessionChair) objects from the conference pending manager
            # list and from the this index (PendingManagersHolder).
            e.getConference().getPendingQueuesMgr().removePendingManager(e)

    def _sendReminderEmail(self, sb):
        from MaKaC.conference import SessionChair
        if type(sb)==list:
            # Sending email just about the participations of the list "sb" (normally
            # they are sessions from one event)
            notif = _PendingManagerNotification( sb )
            mail.GenericMailer.send( notif )
        elif isinstance(sb, SessionChair):
            # The param "sb" is a SessionChair, so we send an email with the info
            # about all its participations
            psList=self.getPendingByEmail(sb.getEmail())
            if psList != [] and psList is not None:
                notif = _PendingManagerNotification( psList )
                mail.GenericMailer.send( notif )

class _PendingManagerNotification(_PendingNotification):

    def getBody( self ):
        url = urlHandlers.UHUserCreation.getURL()
        url.addParam("cpEmail",self._psList[0].getEmail())
        return """
    You have been added as convener of the following sessions:%s
    And session modification rights have been granted to you.
    Please create an account in Indico in order to use these rights. You can create your account at the following URL:

    <%s>

    *Note that you must use this email address %s when creating the account*

    Best Regards.

    --
    Indico"""%( self._getParticipations(), url, self._psList[0].getEmail() )

    def _getParticipations(self):
        participations="\n\n"
        for conf in self._participationsByConf.keys():
            participations+="""\t\t\t- "Event" \"%s\":\n"""%conf.getTitle()
            for ps in self._participationsByConf[conf]:
                session=ps.getSession()
                participations+="""\t\t\t\t - "Session" \"%s\"\n"""%(session.getTitle())
                accessURL = urlHandlers.UHSessionDisplay.getURL(session)
                participations+="\t\t\t\t - Access: %s\n" % accessURL
        return participations


class PendingManagerReminder(PendingReminder):

    def run(self):
        hasAccount=PendingReminder.run(self)
        if not hasAccount:
            psh=PendingManagersHolder()
            psl=psh.getPendingByEmail(self._email)
            if psl != [] and psl is not None:
                notif = _PendingManagerNotification( psl )
                mail.GenericMailer.send( notif )

    def tearDown(self):
        psh = PendingManagersHolder()
        psl = psh.getPendingByEmail(self._email)
        for e in psl:
            e.getConference().getPendingQueuesMgr().removePendingManager(e)

    def getPendings(self):
        psh=PendingManagersHolder()
        return psh.getPendingByEmail(self._email)
#---END MANAGERS


#---PENDING CONFERENCE MANAGERS
class PendingConfManagersHolder(PendingHolder):

    """ This is an index that holds all the requests to add non existing users in the
        list of avatars with rights to manage.
        Those participants are not Avatars yet (do not have Indico account) and that's why
        they are in this pending queue. So once they become Indico users they will be removed
        from the index"""

    def __init__(self):
        """Index by email of all the requests"""
        self._id="ConfManagers"
        self._idx = indexes.IndexesHolder().getById("pendingConfManagers") # All the pending managers
        self._tasksIdx=indexes.IndexesHolder().getById("pendingConfManagersTasks") # Tasks which send reminder emails periodically asking
                                                                                   # for the creation of one indico account
        self._reminder=PendingConfManagerReminder

    def grantRights(self, av):
        l=self.getPendingByEmail(av.getEmail())
        for e in l:
            conf = e.getConference()
            conf.grantModification(av)
            # the ConfPendingQueuesMgr method "removePendingManager" will remove the Manager
            # (type-ConferenceChair) objects from the conference pending manager
            # list and from the this index (PendingManagersHolder).
            conf.getPendingQueuesMgr().removePendingConfManager(e)

    def _sendReminderEmail(self, sb):
        from MaKaC.conference import ConferenceChair
        if type(sb)==list:
            # Sending email just about the participations of the list "sb" (normally
            # they are sessions from one event)
            notif = _PendingConfManagerNotification( sb )
            mail.GenericMailer.send( notif )
        elif isinstance(sb, ConferenceChair):
            # The param "sb" is a SessionChair, so we send an email with the info
            # about all its participations
            psList=self.getPendingByEmail(sb.getEmail())
            if psList != [] and psList is not None:
                notif = _PendingConfManagerNotification( psList )
                mail.GenericMailer.send( notif )

class _PendingConfManagerNotification(_PendingNotification):
    def getBody( self ):
        url = urlHandlers.UHUserCreation.getURL()
        url.addParam("cpEmail",self._psList[0].getEmail())
        return """
    You have been added as manager of the following Event:%s
    And modification rights have been granted to you.
    Please create an account in Indico in order to use these rights. You can create your account at the following URL:

    <%s>

    *Note that you must use this email address %s when creating the account*

    Best Regards.

    --
    Indico"""%( self._getParticipations(), url, self._psList[0].getEmail() )

    def _getParticipations(self):
        participations="\n\n"
        for conf in self._participationsByConf.keys():
            participations+="""\t\t\t- "Event" \"%s\":\n"""%conf.getTitle()
            accessURL = urlHandlers.UHConferenceDisplay.getURL(conf)
            participations+="\t\t\t- Access: %s\n" % accessURL
        return participations


class PendingConfManagerReminder(PendingReminder):
    def run(self):
        hasAccount=PendingReminder.run(self)
        if not hasAccount:
            psh=PendingConfManagersHolder()
            psl=psh.getPendingByEmail(self._email)
            if psl != [] and psl is not None:
                notif = _PendingConfManagerNotification( psl )
                mail.GenericMailer.send( notif )

    def tearDown(self):
        psh = PendingConfManagersHolder()
        psl = psh.getPendingByEmail(self._email)
        for e in psl:
            e.getConference().getPendingQueuesMgr().removePendingConfManager(e)

    def getPendings(self):
        psh = PendingManagersHolder()
        return psh.getPendingByEmail(self._email)
#---END MANAGERS

#---PENDING COORDINATORS
class PendingCoordinatorsHolder(PendingHolder):

    """ This is an index that holds all the requests to add non existing users in the
        list of avatars with rights to coordinate.
        Those participants are not Avatars yet (do not have Indico account) and that's why
        they are in this pending queue. So once they become Indico users they will be removed
        from the index"""

    def __init__(self):
        """Index by email of all the requests"""
        self._id="Coordinators"
        self._idx = indexes.IndexesHolder().getById("pendingCoordinators") # All the pending coordinators
        self._tasksIdx=indexes.IndexesHolder().getById("pendingCoordinatorsTasks") # Tasks which send reminder emails periodically asking for the creation of one indico account
        self._reminder=PendingCoordinatorReminder

    def grantRights(self, av):
        l=self.getPendingByEmail(av.getEmail())
        for e in l:
            # We must grant the new avatar with submission rights
            session=e.getSession()
            session.addCoordinator(av)
            # the ConfPendingQueuesMgr method "removePendingCoordinator" will remove the Coordinator
            # (type-SessionChair) objects from the conference pending coordinator
            # list and from the this index (PendingCoordinatorsHolder).
            e.getConference().getPendingQueuesMgr().removePendingCoordinator(e)

    def _sendReminderEmail(self, sb):
        from MaKaC.conference import SessionChair
        if type(sb)==list:
            # Sending email just about the participations of the list "sb" (normally
            # they are sessions from one event)
            notif = _PendingCoordinatorNotification( sb )
            mail.GenericMailer.send( notif )
        elif isinstance(sb, SessionChair):
            # The param "sb" is a SessionChair, so we send an email with the info
            # about all its participations
            psList=self.getPendingByEmail(sb.getEmail())
            if psList != [] and psList is not None:
                notif = _PendingCoordinatorNotification( psList )
                mail.GenericMailer.send( notif )

class _PendingCoordinatorNotification(_PendingNotification):

    def getBody( self ):
        url = urlHandlers.UHUserCreation.getURL()
        url.addParam("cpEmail",self._psList[0].getEmail())
        return """
    You have been added as convener of the following sessions:%s
    And session coordination rights have been granted to you.
    Please create an account in Indico in order to use these rights. You can create your account at the following URL:

    <%s>

    *Note that you must use this email address %s when creating your account*

    Best Regards.

    --
    Indico"""%( self._getParticipations(), url, self._psList[0].getEmail() )

    def _getParticipations(self):
        participations="\n\n"
        for conf in self._participationsByConf.keys():
            participations+="""\t\t\t- "Event" \"%s\":\n"""%conf.getTitle()
            for ps in self._participationsByConf[conf]:
                session=ps.getSession()
                participations+="""\t\t\t\t - "Session" \"%s\"\n"""%(session.getTitle())
                accessURL = urlHandlers.UHSessionDisplay.getURL(session)
                participations+="\t\t\t\t - Access: %s\n" % accessURL
        return participations


class PendingCoordinatorReminder(PendingReminder):
    def run(self):
        hasAccount=PendingReminder.run(self)
        if not hasAccount:
            psh = PendingCoordinatorsHolder()
            psl = psh.getPendingByEmail(self._email)
            if psl != [] and psl is not None:
                notif = _PendingCoordinatorNotification(psl)
                mail.GenericMailer.send(notif)

    def tearDown(self):
        psh = PendingCoordinatorsHolder()
        psl = psh.getPendingByEmail(self._email)
        for e in psl:
            e.getConference().getPendingQueuesMgr().removePendingCoordinator(e)

    def getPendings(self):
        psh = PendingCoordinatorsHolder()
        return psh.getPendingByEmail(self._email)

#---END COORDINATORS

#--GENERAL---
class PendingQueuesHolder(object):

    _pendingQueues=[PendingConfManagersHolder, \
                    PendingConfSubmittersHolder, \
                    PendingSubmittersHolder, \
                    PendingManagersHolder, \
                    PendingCoordinatorsHolder]

    def _getAllPendingQueues(cls):
        return cls._pendingQueues
    _getAllPendingQueues=classmethod(_getAllPendingQueues)

    def grantRights(cls, av):
        for pq in cls._getAllPendingQueues():
            pq().grantRights(av)
    grantRights=classmethod(grantRights)

    def getFirstPending(cls, email):
        for pq in cls._getAllPendingQueues():
            l=pq().getPendingByEmail(email)
            if len(l)>0:
                return l[0]
        return None
    getFirstPending=classmethod(getFirstPending)

###---------------------------- Conference Pending Queues ---------------------------------

class ConfPendingQueuesMgr(Persistent):

    def __init__(self, conf):
        self._conf=conf
        self._pendingConfManagers={}
        self._pendingConfSubmitters={}
        self._pendingSubmitters={}
        self._pendingManagers={}
        self._pendingCoordinators={}

    def getConference(self):
        return self._conf

    def getPendingConfManagers(self):
        try:
            if self._pendingConfManagers:
                pass
        except AttributeError:
            self._pendingConfManagers={}
        return self._pendingConfManagers

    def getPendingConfSubmitters(self):
        try:
            if self._pendingConfSubmitters:
                pass
        except AttributeError:
            self._pendingConfSubmitters={}
        return self._pendingConfSubmitters

    def getPendingSubmitters(self):
        return self._pendingSubmitters

    def getPendingManagers(self):
        try:
            if self._pendingManagers:
                pass
        except AttributeError:
            self._pendingManagers={}
        return self._pendingManagers

    def getPendingCoordinators(self):
        try:
            if self._pendingCoordinators:
                pass
        except AttributeError:
            self._pendingCoordinators={}
        return self._pendingCoordinators

    def getPendingConfManagersKeys(self, sort=False):
        if sort:
            from MaKaC.conference import ConferenceChair
            # return keys of contribution participants sorted by name
            keys=[]
            vl=[]
            # flatten the list of lists
            for v in self.getPendingConfManagers().values()[:]:
                vl.extend(v)
            # sort
            vl.sort(ConferenceChair._cmpFamilyName)
            for v in vl:
                email=v.getEmail().lower().strip()
                if email not in keys:
                    keys.append(email)
            return keys
        else:
            keys=self.getPendingConfManagers().keys()
        return keys

    def getPendingConfManagersByEmail(self, email):
        email=email.lower().strip()
        if self.getPendingConfManagers().has_key(email):
            return self._pendingConfManagers[email]
        return []

    def isPendingConfManager(self, cp):
        email=cp.getEmail().lower().strip()
        return cp in self.getPendingConfManagersByEmail(email)

    #----Pending queue for conference submitters-----

    def getPendingConfSubmittersKeys(self, sort=False):
        if sort:
            from MaKaC.conference import ConferenceChair
            # return keys of contribution participants sorted by name
            keys=[]
            vl=[]
            # flatten the list of lists
            for v in self.getPendingConfSubmitters().values()[:]:
                vl.extend(v)
            # sort
            vl.sort(ConferenceChair._cmpFamilyName)
            for v in vl:
                email=v.getEmail().lower().strip()
                if email not in keys:
                    keys.append(email)
            return keys
        else:
            keys=self.getPendingConfSubmitters().keys()
        return keys

    def addSubmitter(self, ps, owner, sendEmail=True, sendPeriodicEmail=False):
        from MaKaC.conference import Conference
        if isinstance(owner, Conference):
            self.addPendingConfSubmitter(ps, sendEmail=True, sendPeriodicEmail=False)
            mail.GenericMailer.sendAndLog(_PendingConfSubmitterNotification([ps]), owner)

    def removeSubmitter(self, ps, owner):
        from MaKaC.conference import Conference
        if isinstance(owner, Conference):
            self.removePendingConfSubmitter(ps)

    def addPendingConfManager(self, ps, sendEmail=True, sendPeriodicEmail=False):
        email=ps.getEmail().lower().strip()
        if self.getPendingConfManagers().has_key(email):
            if not ps in self._pendingConfManagers[email]:
                self._pendingConfManagers[email].append(ps)
        else:
            self._pendingConfManagers[email] = [ps]
        pendings=PendingConfManagersHolder()
        pendings.addPending(ps, sendEmail, sendPeriodicEmail)
        self.notifyModification()

    def removePendingConfManager(self, ps):
        email=ps.getEmail().lower().strip()
        if self.getPendingConfManagers().has_key(email):
            if ps in self._pendingConfManagers[email]:
                self._pendingConfManagers[email].remove(ps)
                pendings=PendingConfManagersHolder()
                pendings.removePending(ps)
            if self._pendingConfManagers[email] == []:
                del self._pendingConfManagers[email]
            self.notifyModification()

    def addPendingConfSubmitter(self, ps, sendEmail=True, sendPeriodicEmail=False):
        email=ps.getEmail().lower().strip()
        if self.getPendingConfSubmitters().has_key(email):
            if not ps in self._pendingConfSubmitters[email]:
                self._pendingConfSubmitters[email].append(ps)
        else:
            self._pendingConfSubmitters[email] = [ps]
        pendings=PendingConfSubmittersHolder()
        pendings.addPending(ps, sendEmail, sendPeriodicEmail)
        self.notifyModification()

    def removePendingConfSubmitter(self, ps):
        email=ps.getEmail().lower().strip()
        if self.getPendingConfSubmitters().has_key(email):
            if ps in self._pendingConfSubmitters[email]:
                self._pendingConfSubmitters[email].remove(ps)
                pendings=PendingConfSubmittersHolder()
                pendings.removePending(ps)
            if self._pendingConfSubmitters[email] == []:
                del self._pendingConfSubmitters[email]
            self.notifyModification()

    def getPendingConfSubmittersByEmail(self, email):
        email=email.lower().strip()
        if self.getPendingConfSubmitters().has_key(email):
            return self._pendingConfSubmitters[email]
        return []

    def isPendingConfSubmitter(self, cp):
        email=cp.getEmail().lower().strip()
        return cp in self.getPendingConfSubmittersByEmail(email)

    #---End conference submitters-----


    #----Pending queue for contribution submitters-----

    def getPendingSubmittersKeys(self, sort=False):
        if sort:
            from MaKaC.conference import ContributionParticipation
            # return keys of contribution participants sorted by name
            keys=[]
            vl=[]
            # flatten the list of lists
            for v in self.getPendingSubmitters().values()[:]:
                vl.extend(v)
            # sort
            vl.sort(ContributionParticipation._cmpFamilyName)
            for v in vl:
                email=v.getEmail().lower().strip()
                if email not in keys:
                    keys.append(email)
            return keys
        else:
            keys=self.getPendingSubmitters().keys()
        return keys

    def removePendingSubmitter(self, ps):
        # Used only from contributions.
        # TODO: when refactoring, this method should be renamed and called only from self.removeSubmitter
        email=ps.getEmail().lower().strip()
        if self.getPendingSubmitters().has_key(email):
            if ps in self._pendingSubmitters[email]:
                self._pendingSubmitters[email].remove(ps)
                pendings=PendingSubmittersHolder()
                pendings.removePending(ps)
            if self._pendingSubmitters[email] == []:
                del self._pendingSubmitters[email]
            self.notifyModification()

    def addPendingSubmitter(self, ps, sendEmail=True, sendPeriodicEmail=False):
        # Used only from contributions.
        # TODO: when refactoring, this method should be renamed and called only from self.addSubmitter
        email=ps.getEmail().lower().strip()
        if self.getPendingSubmitters().has_key(email):
            if not ps in self._pendingSubmitters[email]:
                self._pendingSubmitters[email].append(ps)
        else:
            self._pendingSubmitters[email] = [ps]
        pendings=PendingSubmittersHolder()
        pendings.addPending(ps, sendEmail, sendPeriodicEmail)
        self.notifyModification()

    def getPendingSubmittersByEmail(self, email):
        email=email.lower().strip()
        if self.getPendingSubmitters().has_key(email):
            return self._pendingSubmitters[email]
        return []

    def isPendingSubmitter(self, cp):
        email=cp.getEmail().lower().strip()
        return cp in self.getPendingSubmittersByEmail(email)
    #---End submitters-----

    #---Conveners to managers----
    def getPendingManagersKeys(self, sort=False):
        if sort:
            from MaKaC.conference import SessionChair
            # return keys of conveners sorted by name
            keys=[]
            vl=[]
            # flatten the list of lists
            for v in self.getPendingManagers().values()[:]:
                vl.extend(v)
            # sort
            vl.sort(SessionChair._cmpFamilyName)
            for v in vl:
                email=v.getEmail().lower().strip()
                if email not in keys:
                    keys.append(email)
            return keys
        else:
            keys=self.getPendingManagers().keys()
        return keys

    def addPendingManager(self, ps, sendEmail=True, sendPeriodicEmail=False):
        email=ps.getEmail().lower().strip()
        if self.getPendingManagers().has_key(email):
            if not ps in self._pendingManagers[email]:
                self._pendingManagers[email].append(ps)
        else:
            self._pendingManagers[email] = [ps]
        pendings=PendingManagersHolder()
        pendings.addPending(ps, sendEmail, sendPeriodicEmail)
        self.notifyModification()

    def removePendingManager(self, ps):
        email=ps.getEmail().lower().strip()
        if self.getPendingManagers().has_key(email):
            if ps in self._pendingManagers[email]:
                self._pendingManagers[email].remove(ps)
                pendings=PendingManagersHolder()
                pendings.removePending(ps)
            if self._pendingManagers[email] == []:
                del self._pendingManagers[email]
            self.notifyModification()

    def getPendingManagersByEmail(self, email):
        email=email.lower().strip()
        if self.getPendingManagers().has_key(email):
            return self._pendingManagers[email]
        return []

    def isPendingManager(self, cp):
        email=cp.getEmail().lower().strip()
        return cp in self.getPendingManagersByEmail(email)

    #----End managers

    #---Conveners to coordinators----
    def getPendingCoordinatorsKeys(self, sort=False):
        if sort:
            from MaKaC.conference import SessionChair
            # return keys of conveners sorted by name
            keys=[]
            vl=[]
            # flatten the list of lists
            for v in self.getPendingCoordinators().values()[:]:
                vl.extend(v)
            # sort
            vl.sort(SessionChair._cmpFamilyName)
            for v in vl:
                email=v.getEmail().lower().strip()
                if email not in keys:
                    keys.append(email)
            return keys
        else:
            keys=self.getPendingCoordinators().keys()
        return keys

    def addPendingCoordinator(self, ps, sendEmail=True, sendPeriodicEmail=False):
        email=ps.getEmail().lower().strip()
        if self.getPendingCoordinators().has_key(email):
            if not ps in self._pendingCoordinators[email]:
                self._pendingCoordinators[email].append(ps)
        else:
            self._pendingCoordinators[email] = [ps]
        pendings=PendingCoordinatorsHolder()
        pendings.addPending(ps, sendEmail, sendPeriodicEmail)
        self.notifyModification()

    def removePendingCoordinator(self, ps):
        email=ps.getEmail().lower().strip()
        if self.getPendingCoordinators().has_key(email):
            if ps in self._pendingCoordinators[email]:
                self._pendingCoordinators[email].remove(ps)
                pendings=PendingCoordinatorsHolder()
                pendings.removePending(ps)
            if self._pendingCoordinators[email] == []:
                del self._pendingCoordinators[email]
            self.notifyModification()

    def getPendingCoordinatorsByEmail(self, email):
        email=email.lower().strip()
        if self.getPendingCoordinators().has_key(email):
            return self._pendingCoordinators[email]
        return []

    def isPendingCoordinator(self, cp):
        email=cp.getEmail().lower().strip()
        return cp in self.getPendingCoordinatorsByEmail(email)

    #----End coordinators

    def notifyModification(self):
        self._p_changed=1
