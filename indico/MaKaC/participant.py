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

from persistent import Persistent

from MaKaC.common import log
from MaKaC.plugins import Observable
from MaKaC.common.timezoneUtils import nowutc
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.user import Avatar
from MaKaC.webinterface.mail import GenericMailer
from MaKaC.webinterface.mail import GenericNotification
from MaKaC.common import utils
from MaKaC.i18n import _
from indico.core.config import Config
from MaKaC.common.fossilize import fossilizes, Fossilizable
from MaKaC.fossils.participant import IParticipantMinimalFossil

from indico.util.contextManager import ContextManager


class Participation(Persistent, Observable):

    def __init__(self, conference):
        self._conference = conference
        self._obligatory = False
        self._addedInfo = False
        self._allowedForApplying = False
        self._autoAccept = False
        self._participantList = {}
        self._pendingParticipantList = {}
        self._declinedParticipantList = {}
        self._participantIdGenerator = 0
        self._pendingIdGenerator = 0
        self._declinedIdGenerator = 0
        self._displayParticipantList = True
        self._numMaxParticipants = 0
        self._notifyMgrNewParticipant = False

    def clone(self, conference, options, eventManager=None):
        newParticipation = conference.getParticipation()
        newParticipation._obligatory = self._obligatory
        newParticipation._allowedForApplying = self._allowedForApplying
        newParticipation._autoAccept = self.isAutoAccept()
        newParticipation._notifyMgrNewParticipant = self.isNotifyMgrNewParticipant()
        newParticipation._displayParticipantList = self._displayParticipantList
        if options.get("addedInfo", False) :
            newParticipation._addedInfo = True
        clonedStatuses = ["added", "excused", "refused"]
        for p in self._participantList.values():
            if p.getStatus() in clonedStatuses :
                newParticipation.addParticipant(p.clone(conference), eventManager)
        return newParticipation

    def getConference(self):
        return self._conference

    def isObligatory(self):
        return self._obligatory

    def setObligatory(self, responsibleUser = None):
        self._obligatory = True
        logData = {}
        logData["subject"] = "Event set to MANDATORY"
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)

    def setInobligatory(self, responsibleUser = None):
        self._obligatory = False
        logData = {}
        logData["subject"] = "Event set to NON MANDATORY"
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)

    def isAddedInfo(self):
        return self._addedInfo

    def setAddedInfo(self, responsibleUser = None):
        self._addedInfo = True
        logData = {}
        logData["subject"] = "Info about adding WILL be sent to participants"
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)

    def setNoAddedInfo(self, responsibleUser = None):
        self._addedInfo = False
        logData = {}
        logData["subject"] = "Info about adding WON'T be sent to participants"
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)

    def isAllowedForApplying(self):
        try :
            if self._allowedForApplying :
                pass
        except AttributeError :
            self._allowedForApplying = False
        return self._allowedForApplying

    def setAllowedForApplying(self, responsibleUser=None):
        self._allowedForApplying = True
        logData = {}
        logData["subject"] = "Applying for participation is ALLOWED"
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)
        self.notifyModification()

    def setNotAllowedForApplying(self, responsibleUser=None):
        self._allowedForApplying = False
        logData = {}
        logData["subject"] = "Applying for participation is NOT ALLOWED"
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)
        self.notifyModification()

    def isAutoAccept(self):
        try:
            return self._autoAccept
        except AttributeError :
            self._autoAccept = False
            return False

    def setAutoAccept(self, value, responsibleUser = None):
        self._autoAccept = value
        logData = {
            "subject": "Auto accept of participation.",
            "value": str(value)
        }
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)
        self.notifyModification()

    def getNumMaxParticipants(self):
        try:
            return self._numMaxParticipants
        except AttributeError :
            self._numMaxParticipants = 0
            return False

    def setNumMaxParticipants(self, value, responsibleUser = None):
        self._numMaxParticipants = value
        logData = {
            "subject": "Num max of participants.",
            "value": str(value)
        }
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)
        self.notifyModification()

    def isNotifyMgrNewParticipant(self):
        try:
            return self._notifyMgrNewParticipant
        except AttributeError:
            self._notifyMgrNewParticipant = False
            return False

    def setNotifyMgrNewParticipant(self, value):
        currentUser = ContextManager.get('currentUser')
        self._notifyMgrNewParticipant = value
        logData = {}

        if value:
            logData["subject"] = _("Manager notification of participant application has been enabled")
        else:
            logData["subject"] = _("Manager notification of participant application has been disabled")

        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)
        self.notifyModification()

    def isFull(self):
        if self.getNumMaxParticipants() != 0:
            return len(self.getParticipantList()) >= self.getNumMaxParticipants()
        return False

    def alreadyParticipating(self, participant):
        if participant is None :
            return -1
        if participant.getConference().getId() != self.getConference().getId() :
            return -1
        if participant.getId() in self._participantList.keys() :
            return 1
        if participant.getEmail().strip() == "":
            return 0
        for p in self._participantList.values() :
            pString = p.getEmail()
            newString = participant.getEmail()
            if pString == newString :
                return 1
        return 0

    def alreadyPending(self, pending):
        if pending is None :
            return -1
        if pending.getConference().getId() != self.getConference().getId() :
            return -1
        if pending.getId() in self._pendingParticipantList.keys() :
            return 1
        if pending.getEmail().strip() == "":
            return -1
        for p in self._pendingParticipantList.values() :
            if p.getEmail() == pending.getEmail() :
                return 1
        return 0

    def getParticipantList(self):
        participants = self._participantList.values()
        participants.sort(utils.sortUsersByName)
        return participants

    def getPresentParticipantListText(self):
        text = []
        for p in self.getParticipantList():
            if p.isPresent() and p.isConfirmed():
                part = p.getName()
                text.append(part)
        return "; ".join(text)

    def getParticipantById(self, participantId):
        if participantId is not None:
            return self._participantList.get(participantId, None)
        else:
            return None

    def getPendingParticipantList(self):
        return self._pendingParticipantList

    def getPendingParticipantByKey(self, key):
        if key is not None :
            return self._pendingParticipantList.get(key, None)
        else :
            return None

    def prepareAddedInfo(self, participant, eventManager):
        if participant is None :
            return None
        if eventManager is None :
            return None

        data = {}
        title = ""
        familyName = ""
        firstName = ""
        refuse = ""

        refuseURL = urlHandlers.UHConfParticipantsRefusal.getURL( self._conference )
        refuseURL.addParam("participantId","%d"%self._lastParticipantId())
        eventURL = urlHandlers.UHConferenceDisplay.getURL( self._conference )

        toList = []
        if participant.getAvatar() is not None :
            toList.append(participant.getAvatar().getEmail())
            data["toList"] = toList
            title = participant.getAvatar().getTitle()
            familyName = participant.getAvatar().getFamilyName()
            firstName = participant.getAvatar().getFirstName()
        else :
            toList.append(participant.getEmail())
            data["toList"] = toList
            title = participant.getTitle()
            familyName = participant.getFamilyName()
            firstName = participant.getFamilyName()
        if data["toList"] is None or len(data["toList"]) == 0 :
            return None

        if title is None or title == "" :
            title = firstName
        if not self._obligatory :
            refuse = _("""
            If you are not interested in taking part in this event
            or cannot participate due to any reason, please indicate your decline
            to the event organisers at %s
            """)%refuseURL
        else :
            refuse = _("""
            Due to decision of the organisers, presence in the event
            is obligatory for all participants.
            """)

        data["fromAddr"] = eventManager.getEmail()
        data["subject"] = "Invitation to '%s'" % self._conference.getTitle()
        data["body"] = """
        Dear %s %s,

        you have been added to the list of '%s' participants.
        Further information on this event are avaliable at %s.
        %s
        Looking forward to meeting you at %s
        Your Indico
        on behalf of %s %s
        """ % (title, familyName,
               self._conference.getTitle(),
               eventURL, refuse,
               self._conference.getTitle(),
               eventManager.getFirstName(), eventManager.getFamilyName())

        return data

    def getDeclinedParticipantList(self):
        try:
            return self._declinedParticipantList
        except AttributeError :
            self._declinedParticipantList = {}
        return self._declinedParticipantList

    def declineParticipant(self, participant, responsibleUser = None):
        if participant.getConference().getId() != self._conference.getId() :
            return False
        self.removePendingParticipant(participant)
        self.getDeclinedParticipantList()["%d"%self._newDeclinedId()] = participant
        logData = participant.getParticipantData()
        logData["subject"] = _("Participant declined : %s")%participant.getWholeName()
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)
        self.notifyModification()


    def getDeclinedParticipantByKey(self, key):
        if key is not None :
            return self.getDeclinedParticipantList().get(key, None)
        else :
            return None

    def addParticipant(self, participant, eventManager = None):
        # check if it's worth to add the participant
        if participant.getConference().getId() != self._conference.getId() :
            return False
        self.removePendingParticipant(participant)
        if not participant.setId(self._newParticipantId()):
            return False
        if self.alreadyParticipating(participant) != 0 :
            return False
        self._participantList["%d"%self._lastParticipantId()] = participant

        # remove him from the "pending" list
        if participant in self._pendingParticipantList.values() :
            for k in self._pendingParticipantList.keys() :
                if self._pendingParticipantList[k] == participant :
                    del self._pendingParticipantList[k]
                    break

        logData = participant.getParticipantData()
        logData["subject"] = _("New participant added : %s")%participant.getWholeName()
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)

        participant.setStatusAdded()

        # check if an e-mail should be sent...
        if self._addedInfo :
            # to notify the user of his/her addition
            if eventManager is None :
                return False
            data = self.prepareAddedInfo(participant, eventManager)
            GenericMailer.sendAndLog(GenericNotification(data),
                                     self._conference,
                                     log.ModuleNames.PARTICIPANTS)

        avatar = participant.getAvatar()

        if avatar is None :
            # or to encourage him/her to register at Indico
            #self.sendEncouragementToCreateAccount(participant)
            pass
        else:
            # OK, if we have an avatar, let's keep things consistent
            avatar.linkTo(self._conference,"participant")

        self.notifyModification()
        return True

    def inviteParticipant(self, participant, eventManager):
        if participant.getConference().getId() != self._conference.getId() :
            return False
        if not participant.setId(self._newParticipantId()):
            return False
        if eventManager is None :
            return False
        if self.alreadyParticipating(participant) != 0 :
            return False
        self._participantList["%d"%self._lastParticipantId()] = participant
        logData = participant.getParticipantData()
        logData["subject"] = _("New participant invited : %s")%participant.getWholeName()
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)
        participant.setStatusInvited()
        if participant.getAvatar() is not None:
            if not participant.getAvatar().getEmail():
                return False
        else :
            if not participant.getEmail() or participant.getEmail() == "":
                return False
        self.notifyModification()
        return True

    def removeParticipant(self, participant, responsibleUser=None):
        if participant is None:
            return False
        # If 'participant' is an object from Participant
        if isinstance(participant, Participant):
            # remove all entries with participant
            for key, value in self._participantList.items():
                if value == participant:
                    del self._participantList[key]
        # If 'participant' is a key
        else:
            key = participant
            if key not in self._participantList:
                return False
            participant = self._participantList[key]
            del self._participantList[key]

        logData = participant.getParticipantData()
        logData["subject"] = _("Removed participant %s %s (%s)")%(participant.getFirstName(),participant.getFamilyName(),participant.getEmail())
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)

        avatar = participant.getAvatar()
        if avatar:
            avatar.unlinkTo(self._conference,"participant")
        self._notify('participantRemoved', self._conference, participant)
        self.notifyModification()
        return True

    def setParticipantAccepted(self, participantId):
        participant = self.getParticipantById(participantId)
        if participant:
            status = participant.setStatusAccepted()
            self.notifyModification()
            return status
        return None

    def setParticipantRejected(self, participantId):
        participant = self.getParticipantById(participantId)
        if participant:
            status = participant.setStatusRejected()
            self.notifyModification()
            return status
        return None

    def addPendingParticipant(self, participant):
        if participant.getConference().getId() != self._conference.getId() :
            return False
        if participant.getId() is not None :
            return False
        if self.alreadyParticipating(participant) != 0 :
            return False
        if self.isAutoAccept():
            self.addParticipant(participant)
        else:
            self._pendingParticipantList["%d"%self._newPendingId()] = participant

            logData = participant.getParticipantData()
            logData["subject"] = _("New pending participant : %s")%participant.getWholeName()
            self._conference.getLogHandler().logAction(logData,
                                                       log.ModuleNames.PARTICIPANTS)

            participant.setStatusPending()

            profileURL = urlHandlers.UHConfModifParticipantsPending.getURL(self._conference)

            toList = []
            creator=self._conference.getCreator()
            if isinstance(creator, Avatar) :
                toList.append(creator.getEmail())
            for manager in self._conference.getAccessController().getModifierList() :
                if isinstance(manager, Avatar) :
                    toList.append(manager.getEmail())

            data = {}
            data["toList"] = toList
            data["fromAddr"] = Config.getInstance().getSupportEmail()
            data["subject"] = _("New pending participant for %s")%self._conference.getTitle()
            data["body"] = """
            Dear Event Manager,

            a new person is asking for participation in %s.
            Personal profile of this pending participant is available at %s
            Please take this candidature into consideration and accept or reject it

            Your Indico
            """%(self._conference.getTitle(), profileURL)

            GenericMailer.send(GenericNotification(data))
            self.notifyModification()
        return True

    def removePendingParticipant(self, participant, responsibleUser=None):
        if participant is None:
            return False
        if isinstance(participant, Participant):
            # remove all entries with participant
            for key, value in self._pendingParticipantList.items():
                if value == participant:
                    del self._pendingParticipantList[key]
        else:
            key = participant
            if key == "":
                return False
            participant = self._pendingParticipantList[key]
            del self._pendingParticipantList[key]

        logData = participant.getParticipantData()
        logData["subject"] = _("Pending participant removed : %s")%participant.getWholeName()
        self._conference.getLogHandler().logAction(logData,
                                                   log.ModuleNames.PARTICIPANTS)

        self.notifyModification()
        return True

    def setPendingDeclined(self, pendingId):
        return self._pendingParticipantList[pendingId].setStatusDeclined()
        self.notifyModification()

    def setPendingAdded(self, pendingId):
        return self.addParticipant(self._pendingParticipantList[pendingId])
        self.notifyModification()

    def prepareAskForExcuse(self, eventManager, toIdList):
        if eventManager is None :
            return None
        if toIdList is None :
            return None
        if not self._obligatory :
            return None

        if nowutc() < self._conference.getEndDate() :
            return None

        toList = []
        for id in toIdList :
            p = self._participantList[id]
            if not p.isPresent() :
                toList.append(p)
        if len(toList) == 0 :
            return None

        data = {}
        data["toList"] = toList
        data["fromAddr"] = eventManager.getEmail()
        data["subject"] = _("Please excuse your absence to %s")%self._conference.getTitle()
        data["body"] = """
Dear Participant,

you were absent to %s, which was mandatory for you to attend.
Therefore %s %s, the organiser of this event is kindly asking you to provide reasons
for your absence, so that it could be excused - simply by replying to
this email.

Your Indico
on behalf of %s %s
        """%(self._conference.getTitle(), \
        eventManager.getFirstName(), eventManager.getFamilyName(), \
        eventManager.getFirstName(), eventManager.getFamilyName())

        return data

    def askForExcuse(self, eventManager, toIdList):
        data = self.prepareAskForExcuse(eventManager, toIdList)
        if data is None :
            return False

        GenericMailer.sendAndLog(GenericNotification(data), self._conference,
                                 log.ModuleNames.PARTICIPANTS)
        return True

    def sendSpecialEmail(self, participantsIdList, eventManager, data):
        if participantsIdList is None :
            return False
        if eventManager is None :
            return False
        if len(participantsIdList) == 0:
            return True
        if data.get("subject", None) is None :
            return False
        if data.get("body", None) is None :
            return False
        data["fromAddr"] = eventManager.getEmail()

        toList = []
        for userId in participantsIdList :
            participant = self._participantList.get(userId, None)
            if participant is not None :
                toList.append(participant.getEmail())
        data["toList"] = toList
        GenericMailer.sendAndLog(GenericNotification(data), self._conference,
                                 log.ModuleNames.PARTICIPANTS)
        return True

    def getPresentNumber(self):
        counter = 0
        for p in self._participantList.values() :
            if p.isPresent() and p.isConfirmed():
                counter += 1
        return counter

    def getAbsentNumber(self):
        counter = 0
        for p in self._participantList.values() :
            if not p.isPresent() and p.isConfirmed():
                counter += 1
        return counter

    def getExcusedNumber(self):
        counter = 0
        for p in self._participantList.values() :
            if "excused" == p.getStatus() :
                counter += 1
        return counter

    def getInvitedNumber(self):
        counter = 0
        for p in self._participantList.values() :
            if "invited" == p.getStatus() :
                counter += 1
        return counter

    def getRejectedNumber(self):
        counter = 0
        for p in self._participantList.values() :
            if "rejected" == p.getStatus() :
                counter += 1
        return counter

    def getAddedNumber(self):
        counter = 0
        for p in self._participantList.values() :
            if "added" == p.getStatus() :
                counter += 1
        return counter

    def getRefusedNumber(self):
        counter = 0
        for p in self._participantList.values() :
            if "excused" == p.getStatus() :
                counter += 1
        return counter

    def getPendingNumber(self):
        counter = 0
        for part in self._pendingParticipantList.values():
            if not part.getStatus() == "declined":
                counter += 1
        return counter

    def getDeclinedNumber(self):
        return len(self.getDeclinedParticipantList())

    def _newParticipantId(self):
        self._participantIdGenerator += 1
        return self._participantIdGenerator

    def _lastParticipantId(self):
        return self._participantIdGenerator

    def _newPendingId(self):
        self._pendingIdGenerator += 1
        return self._pendingIdGenerator

    def _lastPendingId(self):
        return self._pendingIdGenerator

    def _newDeclinedId(self):
        try:
            self._declinedIdGenerator += 1
        except AttributeError:
            self._declinedIdGenerator = 1
        return self._declinedIdGenerator

    def _lastDeclinedId(self):
        try:
            return self._declinedIdGenerator
        except AttributeError:
            self._declinedIdGenerator = 0
        return self._declinedIdGenerator

    def displayParticipantList(self):
        try :
            if self._displayParticipantList :
                pass
        except AttributeError :
            self._displayParticipantList = True
        return self._displayParticipantList

    def participantListDisplay(self):
        self.displayParticipantList()
        self._displayParticipantList = True
        self.notifyModification()

    def participantListHide(self):
        self.displayParticipantList()
        self._displayParticipantList = False
        self.notifyModification()

    def notifyModification(self):
        if self._conference != None:
            self._conference.notifyModification()
        self._p_changed=1

#---------------------------------------------------------------------------------


class Participant(Persistent, Fossilizable):
    """
        Class collecting data about person taking part in meeting / lecture
    """
    fossilizes(IParticipantMinimalFossil)

    def __init__(self, conference, avatar=None):
        if avatar is not None:
            self._id = None
            self._avatar = avatar
            self._firstName = avatar.getFirstName()
            self._familyName = avatar.getFamilyName()
            if self._firstName.strip() == "" and self._familyName.strip() == "":
                self._firstName = "Undefined name"
            self._title = avatar.getTitle()
            self._address = avatar.getAddress()
            self._affiliation = avatar.getAffiliation()
            self._telephone = avatar.getTelephone()
            self._fax = avatar.getFax()
            self._email = avatar.getEmail()

            self._status = None
            self._present = True
            self._participation = None
            if conference is not None :
                self._participation = conference.getParticipation()
        else:
            self._id = None
            self._avatar = None
            self._firstName = ""
            self._familyName = ""
            self._title = ""
            self._address = ""
            self._affiliation = ""
            self._telephone = ""
            self._fax = ""
            self._email = ""

            self._status = None
            self._present = True
            self._participation = None
            if conference is not None:
                self._participation = conference.getParticipation()

    def clone(self, conference):
        newPart = Participant(conference)
        newPart._avatar = self._avatar
        newPart._firstName = self._firstName
        newPart._familyName = self._familyName
        newPart._title = self._title
        newPart._address = self._address
        newPart._affiliation = self._affiliation
        newPart._telephone = self._telephone
        newPart._fax = self._fax
        newPart._email = self._email
        newPart._status = None
        newPart._present = True

        return newPart


    def getId(self):
        return self._id

    def setId(self, id):
        if self._id is not None :
            return False
        self._id = id
        return True

    def getAvatar(self):
        return self._avatar

    def getTitle(self):
        return self._title

    def setTitle(self, title):
        self._title = title

    def getFirstName(self):
        return self._firstName

    def setFirstName(self, firstName):
        self._firstName = firstName

    def getFamilyName(self):
        return self._familyName

    def setFamilyName(self, familyName):
        self._familyName = familyName

    def getWholeName(self):
        return "%s %s %s"%(self._title,self._firstName,self._familyName)

    def getFullName(self):
        return self.getWholeName()

    def getName(self):
        return "%s %s"%(self.getFirstName(),self.getFamilyName())

    def getAddress(self):
        return self._address

    def setAddress(self, address):
        self._address = address

    def getAffiliation(self):
        return self._affiliation

    def setAffiliation(self, affiliation):
        self._affiliation = affiliation

    def getTelephone(self):
        return self._telephone

    def setTelephone(self, telephone):
        self._telephone = telephone

    def getFax(self):
        return self._fax

    def setFax(self, fax):
        self._fax = fax

    def getEmail(self):
        return self._email

    def setEmail(self, email):
        self._email = email

    def getParticipantData(self):
        data = {}
        data["Title"] = self.getTitle()
        data["Family name"] = self.getFamilyName()
        data["First name"] = self.getFirstName()
        data["Affiliation"] = self.getAffiliation()
        data["Address"] = self.getAddress()
        data["Email"] = self.getEmail()
        data["Phone"] = self.getTelephone()
        data["Fax"] = self.getFax()
        data["Participant status"] = self.getStatus()

        return data

    def isPresent(self):
        return self._present

    def setPresent(self):
        self._present = True

    def setAbsent(self):
        self._present = False

    def getParticipation(self):
        return self._participation

    def getConference(self):
        return self._participation.getConference()

    def getStatus(self):
        return self._status

    def isConfirmed(self):
        return self._status in ["accepted", "added"]

    def setStatusAdded(self, responsibleUser=None):
        self._status = "added"
        #if self._status is None or self._status == "pending" :
        #    self._status = "added"
        #
        #    logData = self.getParticipantData()
        #    logData["subject"] = _("%s : status set to ADDED")%self.getWholeName()
        #    self.getConference().getLogHandler().logAction(logData,"participants",responsibleUser)

        self._participation._notify('participantAdded', self.getConference(), self)
        logData = self.getParticipantData()
        logData["subject"] = "%s : status set to ADDED"%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,
                                                       log.ModuleNames.PARTICIPANTS)

        return True

    def setStatusRefused(self, responsibleUser=None):
        if self._status != "added" :
            return False
        self._status = "refused"

        self._participation._notify('participantRemoved', self.getConference(), self)
        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to REFUSED")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,
                                                       log.ModuleNames.PARTICIPANTS)

        return True

    def setStatusExcused(self, responsibleUser=None):
        if not self.isConfirmed() or self._present:
            return False
        self._status = "excused"

        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to EXCUSED")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,
                                                       log.ModuleNames.PARTICIPANTS)

        return True

    def setStatusInvited(self, responsibleUser=None):
        if self._status is not None :
            return False
        self._status = "invited"

        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to INVITED")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,
                                                       log.ModuleNames.PARTICIPANTS)

        return True

    def setStatusAccepted(self, responsibleUser=None):
        if self._status not in ('invited', 'added'):
            return False
        self._status = "accepted"

        self._participation._notify('participantAdded', self.getConference(), self)
        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to ACCEPTED")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,
                                                       log.ModuleNames.PARTICIPANTS)

        return True

    def setStatusRejected(self, responsibleUser=None):
        if self._status not in ('invited', 'added'):
            return False
        self._status = "rejected"

        self._participation._notify('participantRemoved', self.getConference(), self)
        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to REJECTED")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,
                                                       log.ModuleNames.PARTICIPANTS)

        return True

    def setStatusPending(self, responsibleUser=None):
        if self._status is not None :
            return False
        self._status = "pending"

        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to PENDING")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,
                                                       log.ModuleNames.PARTICIPANTS)

        return True

    def setStatusDeclined(self, responsibleUser=None):
        if self._status != "pending" :
            return False
        self._status = "declined"

        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to DECLINED")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,
                                                       log.ModuleNames.PARTICIPANTS)

        return True


#---------------------------------------------------------------------------------
