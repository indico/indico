# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from persistent import Persistent

from MaKaC.common import indexes, mail
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.mail import GenericNotification

from indico.core import signals
from indico.core.config import Config
from indico.core.logger import Logger
from indico.modules.auth.util import url_for_register


logger = Logger.get('pending')


class PendingHolder(object):
    """ This is an index that holds all the requests to add pending people to become
        Indico users.
        Those participants are not Avatars yet (do not have Indico account) and that's why
        they are in this pending queue. So once they become Indico users they will be removed
        from the index"""

    def __init__(self):
        """Index by email of all the request and all the tasks with the reminders"""
        self._id = ""
        self._idx = None  # All the pending users

    def getPendingByEmail(self, email):
        return self._idx.matchPendingUser(email)

    def removePending(self, sb):
        """Remove the pendant from the queue"""
        self._idx.unindexPendingUser(sb)

    def addPending(self, sb, sendEmail=True):
        """Add a new user to the index"""
        self._idx.indexPendingUser(sb)
        if sendEmail:
            self._sendReminderEmail(sb)

    def grantRights(self, av):
        """We must implement this method in order to grant the specific rights to the new user"""
        pass

    def _sendReminderEmail(self, sb):
        """We must implement this method in order to sent an email with the reminder for the specific pending users"""
        pass


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


#---END GENERAL


#---SUBMITTERS----


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
        # we go to the login page since local registration might be disabled
        # in the future it would be nice to use a different messages depending
        # if local identities are enabled or not
        url = url_for_register()
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
        # we go to the login page since local registration might be disabled
        # in the future it would be nice to use a different messages depending
        # if local identities are enabled or not
        url = url_for_register()
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
        # we go to the login page since local registration might be disabled
        # in the future it would be nice to use a different messages depending
        # if local identities are enabled or not
        url = url_for_register()
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



#---END COORDINATORS

###---------------------------- Conference Pending Queues ---------------------------------

class ConfPendingQueuesMgr(Persistent):

    def __init__(self, conf):
        self._conf=conf
        self._pendingSubmitters={}
        self._pendingManagers={}
        self._pendingCoordinators={}

    def getConference(self):
        return self._conf

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

    def addPendingSubmitter(self, ps, sendEmail=True):
        # Used only from contributions.
        # TODO: when refactoring, this method should be renamed and called only from self.addSubmitter
        email=ps.getEmail().lower().strip()
        if self.getPendingSubmitters().has_key(email):
            if not ps in self._pendingSubmitters[email]:
                self._pendingSubmitters[email].append(ps)
        else:
            self._pendingSubmitters[email] = [ps]
        pendings=PendingSubmittersHolder()
        pendings.addPending(ps, sendEmail)
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

    def addPendingManager(self, ps, sendEmail=True):
        email=ps.getEmail().lower().strip()
        if self.getPendingManagers().has_key(email):
            if not ps in self._pendingManagers[email]:
                self._pendingManagers[email].append(ps)
        else:
            self._pendingManagers[email] = [ps]
        pendings=PendingManagersHolder()
        pendings.addPending(ps, sendEmail)
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

    def addPendingCoordinator(self, ps, sendEmail=True):
        email=ps.getEmail().lower().strip()
        if self.getPendingCoordinators().has_key(email):
            if not ps in self._pendingCoordinators[email]:
                self._pendingCoordinators[email].append(ps)
        else:
            self._pendingCoordinators[email] = [ps]
        pendings=PendingCoordinatorsHolder()
        pendings.addPending(ps, sendEmail)
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


@signals.users.registered.connect
def _on_user_register(user, **kwargs):
    """Remove newly-added users from pending lists"""
    pending_submitter = PendingSubmittersHolder().getPendingByEmail(user.email)
    if pending_submitter:
        principal = pending_submitter[0]
        mgr = principal.getConference().getPendingQueuesMgr()
        logger.info('Removed pending submitter {0} from {1}'.format(user, principal.getConference()))
        mgr.removePendingSubmitter(principal)
