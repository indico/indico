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

from persistent import Persistent
from datetime import timedelta, datetime
from MaKaC.common.timezoneUtils import nowutc
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.user import Avatar
from MaKaC.negotiations import Negotiator
from MaKaC.webinterface.mail import GenericMailer
from MaKaC.webinterface.mail import GenericNotification
from MaKaC.common import utils
import MaKaC.common.info as info
from MaKaC.i18n import _

class Participation(Persistent):

    def __init__(self, conference):
        self._conference = conference
        self._obligatory = False
        self._addedInfo = False
        self._allowedForApplying = False
        self._autoAccept = False
        self._participantList = {}
        self._pendingParticipantList = {}
        self._participantIdGenerator = 0
        self._pendingIdGenerator = 0
        self._dateNegotiation = None
        self._displayParticipantList = True

    def clone(self, conference, options, eventManager=None):
        newParticipation = conference.getParticipation()
        newParticipation._obligatory = self._obligatory
        newParticipation._allowedForApplying = self._allowedForApplying
        newParticipation._autoAccept = self._autoAccept
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
        self._conference.getLogHandler().logAction(logData,"participants",responsibleUser)

    def setInobligatory(self, responsibleUser = None):
        self._obligatory = False
        logData = {}
        logData["subject"] = "Event set to NON MANDATORY"
        self._conference.getLogHandler().logAction(logData,"participants",responsibleUser)

    def isAddedInfo(self):
        return self._addedInfo

    def setAddedInfo(self, responsibleUser = None):
        self._addedInfo = True
        logData = {}
        logData["subject"] = "Info about adding WILL be sent to participants"
        self._conference.getLogHandler().logAction(logData,"participants",responsibleUser)

    def setNoAddedInfo(self, responsibleUser = None):
        self._addedInfo = False
        logData = {}
        logData["subject"] = "Info about adding WON'T be sent to participants"
        self._conference.getLogHandler().logAction(logData,"participants",responsibleUser)

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
        self._conference.getLogHandler().logAction(logData,"participants",responsibleUser)
        self.notifyModification()

    def setNotAllowedForApplying(self, responsibleUser=None):
        self._allowedForApplying = False
        logData = {}
        logData["subject"] = "Applying for participation is NOT ALLOWED"
        self._conference.getLogHandler().logAction(logData,"participants",responsibleUser)
        self.notifyModification()

    def getAutoAccept(self):
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
        self._conference.getLogHandler().logAction(logData, "participants", responsibleUser)
        self.notifyModification()

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

    def getParticipantListText(self):
        text = []
        for p in self.getParticipantList():
            part = p.getName()
            if not p.isPresent() and nowutc() > self._conference.getEndDate():
                part += " (absent)"
            text.append(part)
        return "; ".join(text)

    def getPresentParticipantListText(self):
        text = []
        for p in self.getParticipantList():
            if p.isPresent() or nowutc() < self._conference.getEndDate():
                part = p.getName()
                text.append(part)
        return "; ".join(text)

    def getParticipantById(self, participantId):
        if participantId is not None :
            return self._participantList.get(participantId, None)
        else :
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
        data["subject"] = _("Invitation to %s")%self._conference.getTitle()
        data["body"] = _("""
        Dear %s %s,

        you have been added to the list of '%s' participants.
        Further information on this event are avaliable at %s.
        %s
        Looking forward to meeting you at %s
        Your Indico
        on behalf of %s %s
        """)%(title, familyName, \
             self._conference.getTitle(), \
             eventURL, refuse, \
             self._conference.getTitle(), \
             eventManager.getFirstName(), eventManager.getFamilyName())

        return data


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
        self._conference.getLogHandler().logAction(logData,"participants",eventManager)

        participant.setStatusAdded()

        # check if an e-mail should be sent...
        if self._addedInfo :
            # to notify the user of his/her addition
            if eventManager is None :
                return False
            data = self.prepareAddedInfo(participant, eventManager)
            GenericMailer.sendAndLog(GenericNotification(data),self._conference,"participants")

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
        self._conference.getLogHandler().logAction(logData,"participants",eventManager)
        participant.setStatusInvited()
        data = {}
        title = ""
        firstName = ""
        familyName = ""
        eventURL = urlHandlers.UHConferenceDisplay.getURL( self._conference )
        actionURL = urlHandlers.UHConfParticipantsInvitation.getURL( self._conference )
        actionURL.addParam("participantId","%d"%self._lastParticipantId())
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
        locationName = locationAddress = ""
        if self._conference.getLocation() is not None :
            locationName = self._conference.getLocation().getName()
            locationAddress = self._conference.getLocation().getAddress()
        if data["toList"] is None or len(data["toList"]) == 0 :
            return False
        if title is None or title == "" :
            title = firstName
        data["fromAddr"] = eventManager.getEmail()
        data["subject"] = _("Invitation to %s")%self._conference.getTitle()
        data["body"] = _("""
        Dear %s %s,

        %s %s, event manager of '%s' would like to invite you to take part in this event,
        which will take place on %s in %s, %s. Further information on this event are
        available at %s
        You are kindly requested to accept or decline your participation in this event by
        clicking on the link below :
         %s

        Looking forward to meeting you at %s
        Your Indico
        on behalf of %s %s

        """)%(title, familyName, \
             eventManager.getFirstName(), eventManager.getFamilyName(), \
             self._conference.getTitle(), \
             self._conference.getAdjustedStartDate(), \
             locationName, locationAddress, \
             eventURL, actionURL, \
             self._conference.getTitle(), \
             eventManager.getFirstName(), eventManager.getFamilyName())
        GenericMailer.sendAndLog(GenericNotification(data),self._conference,"participants")
        #if participant.getAvatar() is None :
        #    self.sendEncouragementToCreateAccount(participant)
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
        self._conference.getLogHandler().logAction(logData,"participants",responsibleUser)

        avatar = participant.getAvatar()
        if avatar:
            avatar.unlinkTo(self._conference,"participant")

        self.notifyModification()
        return True

    def setParticipantRefused(self, participantId):
        return self._participantList[participantId].setStatusRefused()
        self.notifyModification()

    def setParticipantExcused(self, participantId):
        return self._participantList[participantId].setStatusExcused()
        self.notifyModification()

    def setParticipantAccepted(self, participantId):
        return self._participantList[participantId].setStatusAccepted()
        self.notifyModification()

    def setParticipantRejected(self, participantId):
        return self._participantList[participantId].setStatusRejected()
        self.notifyModification()

    def addPendingParticipant(self, participant):
        if participant.getConference().getId() != self._conference.getId() :
            return False
        if participant.getId() is not None :
            return False
        if self.alreadyParticipating(participant) != 0 :
            return False
        if self.getAutoAccept():
            self.addParticipant(participant)
        else:
            self._pendingParticipantList["%d"%self._newPendingId()] = participant

            logData = participant.getParticipantData()
            logData["subject"] = _("New pending participant : %s")%participant.getWholeName()
            self._conference.getLogHandler().logAction(logData,"participants")

            participant.setStatusPending()

            profileURL = urlHandlers.UHConfModifParticipantsPendingDetails.getURL(self._conference)
            profileURL.addParam("pendingId", self._lastPendingId())

            toList = []
            creator=self._conference.getCreator()
            if isinstance(creator, Avatar) :
                toList.append(creator.getEmail())
            for manager in self._conference.getAccessController().getModifierList() :
                if isinstance(manager, Avatar) :
                    toList.append(manager.getEmail())

            data = {}
            data["toList"] = toList
            data["fromAddr"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
            data["subject"] = _("New pending participant for %s")%self._conference.getTitle()
            data["body"] = _("""
            Dear Event Manager,

            a new person is asking for participation in %s.
            Personal profile of this pending participant is available at %s
            Please take this candidature into consideration and accept or reject it

            Your Indico
            """)%(self._conference.getTitle(), profileURL)

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
        self._conference.getLogHandler().logAction(logData,"participants",responsibleUser)

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
                toList.append(p.getEmail())
        if len(toList) == 0 :
            return None

        data = {}
        data["toList"] = toList
        data["fromAddr"] = eventManager.getEmail()
        data["subject"] = _("Please excuse your absence to %s")%self._conference.getTitle()
        data["body"] = _("""
Dear Participant,

you were absent to %s, which was mandatory for you to attend.
Therefore %s %s, the organiser of this event is kindly asking you to provide reasons
for your absence, so that it could be excused - simply by replying to
this email.

Your Indico
on behalf of %s %s
        """)%(self._conference.getTitle(), \
        eventManager.getFirstName(), eventManager.getFamilyName(), \
        eventManager.getFirstName(), eventManager.getFamilyName())

        return data

    def askForExcuse(self, eventManager, toIdList):
        data = self.prepareAskForExcuse(eventManager,toIdList)
        if data is None :
            return False

        GenericMailer.sendAndLog(GenericNotification(data),self._conference,"participants",eventManager)
        return True

    def sendSpecialEmail(self, participantsIdList, eventManager, data):
        if participantsIdList is None :
            return False
        if eventManager is None :
            return False
        if len(participantsIdList) == 0:
            return True
        if data.get("subject",None) is None :
            return False
        if data.get("body",None) is None :
            return False
        data["fromAddr"] = eventManager.getEmail()

        toList = []
        for id in participantsIdList :
            participant = self._participantList.get(id,None)
            if Participant is not None :
                toList.append(p.getEmail())
        data["toList"] = toList
        GenericMailer.sendAndLog(GenericNotification(data),self._conference,"participants",eventManager)
        return True

    def sendEncouragementToCreateAccount(self, participant):
        if participant is None :
            return False
        if participant.getEmail() is None or participant.getEmail() == "" :
            return None
        data = {}
        title = participant.getTitle()
        if title is None or title == "" :
            title = participant.getFirstName()

        createURL = urlHandlers.UHUserCreation.getURL()
        data["fromAddr"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getNoReplyEmail(returnSupport=True)
        toList = []
        toList.append(participant.getEmail())
        data["toList"] = toList
        data["subject"] = _("Invitation to create an Indico account")
        data["body"] = _("""
        Dear %s %s,

        You have been added as a participant to '%s' and you have started to use
        the Indico system. Most probably you are going to use it in the future,
        participating in other events supported by Indico.
        Therefore we strongly recommend that you create your personal Indico Account -
        storing your personal data it will make your work with Indico easier and
        allow you access more sophisticated features of the system.

        To proceed in creating your Indico Account simply click on the following
        link : %s
        Please use this email address when creating your account: %s

        Your Indico
        """)%(participant.getFirstName(), participant.getFamilyName(), \
        self._conference.getTitle(), \
        createURL, participant.getEmail())

        GenericMailer.sendAndLog(GenericNotification(data),self._conference,"participants")
        return True

    def sendNegotiationInfo(self):
        if self._dateNgotiation is None :
            return False
        if not self._dateNegotiation.isFinished() :
            return False

        data = {}
        data["fromAddr"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getNoReplyEmail(returnSupport=True)
        if len(self._dateNegotiation.getSolutionList()) == 0:

            """ TODO: Prepate URLs..!! """

            settingURL = ">>must be prepared yet..!!<<"
            data["subject"] = _("Negotiation algorithm finished - FAILED to find date")
            toList = []
            for manager in self._conference.getManagerList() :
                if isinstance(manager, Avatar) :
                    toList.append(manager.getEmail())
            data["toList"] = toList
            data["body"] = _("""
            Dear Event Manager,

            negotiation algorithm has finished its work on finding the date for %s,
            yet it didn't managed to find any solution satisfying all (or almost all)
            given restrictions.
            Setting the event's date is now up to you at %s

            Your Indico
            """)%(self._conference.getTitle(), settingURL)

        elif not self.dateNegotiation.isAutomatic :
            """ TODO: Prepate URLs..!! """

            choseURL = ">>must be prepared yet..!!<<"
            data["subject"] = _("Negotiation algorithm finished - SUCCSEEDED")
            toList = []
            for manager in self._conference.getManagerList() :
                if isinstance(manager, Avatar) :
                    toList.append(manager.getEmail())
            data["toList"] = toList
            data["body"] = _("""
            Dear Event Manager,

            negotiation algorithm has finished its work on finding the date for %s,
            now you are kindly requested to choose the most siutable date from
            the list of solution which is avaliable at %s

            Your Indico
            """)%(self._conference.getTitle(), choseURL)

        else :
            data["subject"] = _("Date of the %s setteled")%self._conference.getTitle()
            toList = []
            for p in self._participantList.valuess() :
                toList.append(p.getEmail())
            data["toList"] = toList
            data["body"] = _("""
            Dear Participant,

            negotiation algorithm has just set the date of the %s to :
                start date : %s
                end date   : %s

            Wishing you a pleasent and interesting time -
            Your Indico
            """)%(self._conference.getTitle(), \
            self._conference.getAdjustedStartDate(), self._conference.getAdjustedEndDate())

        GenericMailer.send(GenericNotification(data))
        return True

    def getPresentNumber(self):
        counter = 0
        for p in self._participantList.values() :
            if p.isPresent() :
                counter += 1
        return counter

    def getAbsentNumber(self):
        counter = 0
        for p in self._participantList.values() :
            if not p.isPresent() :
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

class Participant (Persistent, Negotiator):
    """
        Class collecting data about person taking part in meeting / lecture
    """

    def __init__(self, conference, avatar=None):
        Negotiator(avatar)
        if avatar is not None :
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
        else :
            Negotiator(None)
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
            self._present = None
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

    def getNegotiatorInfo(self):
        return "%s %s %s"%(self._firstName,self._familyName,self._email)

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

    def setStatusAdded(self, responsibleUser=None):
        self._status = "added"
        #if self._status is None or self._status == "pending" :
        #    self._status = "added"
        #
        #    logData = self.getParticipantData()
        #    logData["subject"] = _("%s : status set to ADDED")%self.getWholeName()
        #    self.getConference().getLogHandler().logAction(logData,"participants",responsibleUser)

        logData = self.getParticipantData()
        logData["subject"] = "%s : status set to ADDED"%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,"participants",responsibleUser)

        return True

    def setStatusRefused(self, responsibleUser=None):
        if self._status != "added" :
            return False
        self._status = "refused"

        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to REFUSED")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,"participants",responsibleUser)

        return True

    def setStatusExcused(self, responsibleUser=None):
        if self._status != "added" or self._present :
            return False
        self._status = "excused"

        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to EXCUSED")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,"participants",responsibleUser)

        return True

    def setStatusInvited(self, responsibleUser=None):
        if self._status is not None :
            return False
        self._status = "invited"

        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to INVITED")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,"participants",responsibleUser)

        return True

    def setStatusAccepted(self, responsibleUser=None):
        if self._status != "invited" :
            return False
        self._status = "accepted"

        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to ACCEPTED")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,"participants",responsibleUser)

        return True

    def setStatusRejected(self, responsibleUser=None):
        if self._status != "invited" :
            return False
        self._status = "rejected"

        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to REJECTED")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,"participants",responsibleUser)

        return True

    def setStatusPending(self, responsibleUser=None):
        if self._status is not None :
            return False
        self._status = "pending"

        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to PENDING")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,"participants",responsibleUser)

        return True

    def setStatusDeclined(self, responsibleUser=None, sendMail=True):
        if self._status != "pending" :
            return False
        self._status = "declined"

        logData = self.getParticipantData()
        logData["subject"] = _("%s : status set to DECLINED")%self.getWholeName()
        self.getConference().getLogHandler().logAction(logData,"participants",responsibleUser)

        if sendMail:
            data = {}
            data["fromAddr"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getNoReplyEmail(returnSupport=True)
            confTitle = self._participation.getConference().getTitle()
            data["subject"] = _("Your application for attendance in %s declined")%confTitle
            toList = []
            toList.append(self._email)
            title = ""
            if self._title == "" or self._title is None :
                title = self._firstName
            else:
                title = self._title
            data["toList"] = toList
            data["body"] = _("""
            Dear %s %s,

            your request to attend the %s has been declined by the event manager.

            Your Indico
            """)%(title, self._familyName, confTitle)

            GenericMailer.sendAndLog(GenericNotification(data),self.getConference(),"participants",responsibleUser)

        return True


#---------------------------------------------------------------------------------
