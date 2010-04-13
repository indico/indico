# -*- coding: utf-8 -*-
##
## $Id: registration.py,v 1.57 2009/06/15 14:06:06 jose Exp $
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

import md5, random, time
from datetime import datetime,timedelta
from pytz import timezone
from pytz import all_timezones
from MaKaC.common.timezoneUtils import nowutc
from persistent import Persistent
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList
import MaKaC
from MaKaC.common.Counter import Counter
from MaKaC.errors import FormValuesError,MaKaCError
from MaKaC.common.Locators import Locator
from MaKaC.common import Config
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.webinterface.common.tools import strip_ml_tags
from MaKaC.trashCan import TrashCanManager
from MaKaC.webinterface.mail import GenericMailer, GenericNotification
from MaKaC.i18n import _

import string

def stringToDate( str ):
    months = {  "January":1, "February":2, "March":3, "April":4, "May":5, "June":6, "July":7, "August":8, "September":9, "October":10, "November":11, "December":12 }
    [ day, month, year ] = str.split("-")
    return datetime(int(year),months[month],int(day))

class RegistrationForm(Persistent):

    def __init__(self, conf, groupData=None):
        self._conf = conf
        if groupData is None:
            self.activated = False
            self.title =  _("Registration Form")
            self.announcement = ""
            self.usersLimit = 0
            self.contactInfo = ""
            self.setStartRegistrationDate(nowutc())
            self.setEndRegistrationDate(nowutc())
            self.setModificationEndDate(None)
            self.setCurrency( _("not selected"))
        else:
            self.activated = groupData.get("activated", False)
            self.title = groupData.get("name", "")
            self.announcement = groupData.get("announcement", "")
            self.usersLimit = groupData.get("limit", "")
            self.startRegistrationDate = groupData.get("startRegistrationDate", None)
            if self.startRegistrationDate is None:
                self.setStartRegistrationDate(nowutc())
            self.endRegistrationDate = groupData.get("endRegistrationDate", None)
            if self.endRegistrationDate is None:
                self.setEndRegistrationDate(nowutc())
            self.modificationEndDate = groupData.get("modificationEndDate", None)
            #if self.modificationEndDate is None:
            #    self.setModificationEndDate(nowutc())
            self.contactInfo = groupData.get("contactInfo", "")
            self.setCurrency(groupData.get("Currency", ""))
        self.notification = Notification()
        # Status definition
        self._statuses={}
        self._statusesGenerator=Counter()
        #Multiple-Subforms
        self.personalData = PersonalData()
        #Simple-SubForms
        self.sessionsForm = SessionsForm()
        self.accommodationForm = AccommodationForm(self)
        self.reasonParticipationForm = ReasonParticipationForm()
        self.furtherInformation = FurtherInformationForm()
        self.socialEventForm = SocialEventForm(self)
        #General-SubForms
        self._generalSectionGenerator = Counter()
        self.generalSectionForms={}
        #All SortedForms
        self._sortedForms=[]
        self.addToSortedForms(self.reasonParticipationForm)
        self.addToSortedForms(self.sessionsForm)
        self.addToSortedForms(self.accommodationForm)
        self.addToSortedForms(self.socialEventForm)
        self.addToSortedForms(self.furtherInformation)

        self.setAllSessions()

    def clone(self, conference):
        form = RegistrationForm(conference)
        form.setConference(conference)
        form.setAnnouncement(self.getAnnouncement())
        form.setContactInfo(self.getContactInfo())
        form.setCurrency(self.getCurrency())
        registrationPeriodEnd = self.getConference().getStartDate() - self.getEndRegistrationDate()
        registrationPeriodStart = self.getConference().getStartDate() - self.getStartRegistrationDate()
        form.setEndRegistrationDate(conference.getStartDate() - registrationPeriodEnd)
        form.setStartRegistrationDate(conference.getStartDate() - registrationPeriodStart)
        if self.getModificationEndDate():
            registrationPeriodModifEndDate = self.getConference().getStartDate() - self.getModificationEndDate()
            form.setModificationEndDate(conference.getStartDate() - registrationPeriodModifEndDate)
        form.setTitle(self.getTitle())
        form.setUsersLimit(self.getUsersLimit())
        form.setActivated(self.isActivated())
        form.setMandatoryAccount(self.isMandatoryAccount())
        form.setAllSessions()
        form.notification=self.getNotification().clone()
        acf = self.getAccommodationForm()
        if acf is not None :
            form.accommodationForm = acf.clone(form)
        fif = self.getFurtherInformationForm()
        if fif is not None :
            form.furtherInformation = fif.clone()
        rpf = self.getReasonParticipationForm()
        if rpf is not None :
            form.reasonParticipationForm = rpf.clone()
        ses = self.getSessionsForm()
        if ses is not None :
            form.sessionsForm = ses.clone(conference.getSessionList())
        sef = self.getSocialEventForm()
        if sef is not None :
            form.socialEventForm = sef.clone(form)
        for section in self.getGeneralSectionFormsList():
            newSection = section.clone(form)
            form.generalSectionForms[section.getId()] = newSection
            form.addToSortedForms(newSection)
        del form._sortedForms
        return form

    def getCurrency(self):
        try:
            return self._currency
        except:
            self.setCurrency( _("not selected"))
        return self._currency

    def setCurrency(self, currency):
        self._currency = currency

    def getConference(self):
        return self._conf
    getOwner = getConference

    def getTimezone(self):
        return self.getConference().getTimezone()

    def setConference(self, conf):
        self._conf = conf
    setOwner = setConference

    def setAllSessions(self):
        for ses in self._conf.getSessionList():
            rs = RegistrationSession(ses, self)
            self.sessionsForm.addSession(rs)

    def isActivated(self):
        return self.activated

    def activate(self):
        self.activated = True

    def deactivate(self):
        self.activated = False

    def setActivated(self, value):
        self.activated = value

    def isMandatoryAccount(self):
        try:
            if self._mandatoryAccount:
                pass
        except AttributeError, e:
            self._mandatoryAccount = True
        return self._mandatoryAccount

    def setMandatoryAccount(self, v=True):
        self._mandatoryAccount = v

    def setTitle( self, newName ):
        self.title = newName.strip()

    def getTitle( self ):
        return self.title

    def setAnnouncement( self, newDesc ):
        self.announcement = newDesc.strip()

    def getAnnouncement( self ):
        return self.announcement

    def setUsersLimit( self, newLimit ):
        if isinstance(newLimit, int):
            self.usersLimit = newLimit
        elif isinstance(newLimit, str) :
            if newLimit.strip() == "":
                self.usersLimit = 0
            else:
                self.usersLimit = int(newLimit.strip())
        if self.usersLimit<0: self.usersLimit=0


    def getUsersLimit( self ):
        return self.usersLimit

    def isFull(self):
        if self.usersLimit != 0:
            return len(self.getConference().getRegistrants()) >= self.usersLimit
        return False

    def setStartRegistrationDate( self, sd ):
        self.startRegistrationDate = datetime(sd.year,sd.month,sd.day,0,0,0)

    def getStartRegistrationDate( self ):
        return timezone(self.getTimezone()).localize(self.startRegistrationDate)

    def setEndRegistrationDate( self, ed ):
        self.endRegistrationDate = datetime(ed.year,ed.month,ed.day,23,59,59)

    def getEndRegistrationDate( self ):
        return timezone(self.getTimezone()).localize(self.endRegistrationDate)

    def setModificationEndDate( self, ed ):
        if ed:
            self.modificationEndDate = datetime(ed.year,ed.month,ed.day,23,59,59)
        else:
            self.modificationEndDate = None

    def getModificationEndDate( self ):
        try:
            if self.modificationEndDate:
                return timezone(self.getTimezone()).localize(self.modificationEndDate)
        except AttributeError, e:
            pass
        return None

    def inModificationPeriod(self):
        if self.getModificationEndDate() is None:
            return False
        date=nowutc()
        sd = self.getStartRegistrationDate()
        ed = self.getModificationEndDate()
        return date <= ed and date >= sd

    def inRegistrationPeriod(self, date=None):
        if date is None:
            date=nowutc()
        sd = self.getStartRegistrationDate()
        ed = self.getEndRegistrationDate()
        return date <= ed and date >= sd

    def setContactInfo( self, ci ):
        self.contactInfo = ci

    def getContactInfo( self ):
        return self.contactInfo

    def getStatuses(self):
        try:
            if self._statuses:
                pass
        except AttributeError,e:
            self._statuses={}
        return self._statuses

    def _generateStatusId(self):
        try:
            if self._statusesGenerator:
                pass
        except AttributeError, e:
            self._statusesGenerator = Counter()
        return self._statusesGenerator

    def getStatusesList(self, sort=True):
        v=self.getStatuses().values()
        if sort:
            v.sort(Status._cmpCaption)
        return v

    def getStatusById(self, id):
        if self.getStatuses().has_key(id):
            return self.getStatuses()[id]
        return None

    def addStatus(self, st):
        st.setId( str(self._generateStatusId().newCount()) )
        self.getStatuses()[st.getId()]=st
        self.notifyModification()

    def removeStatus(self, st):
        if self.getStatuses().has_key(st.getId()):
            del self.getStatuses()[st.getId()]
            self.notifyModification()

    def getNotification(self):
        try:
            if self.notification:
                pass
        except:
            self.notification = Notification()
        return self.notification

    def getPersonalData(self):
        return self.personalData

    def getFurtherInformationForm(self):
        return self.furtherInformation

    def getSessionsForm(self):
        return self.sessionsForm

    def getAccommodationForm(self):
        return self.accommodationForm

    def getSocialEventForm(self):
        return self.socialEventForm

    def getReasonParticipationForm(self):
        return self.reasonParticipationForm

    def getSectionById(self, id):
        if id == "reasonParticipation":
            return self.getReasonParticipationForm()
        if id == "sessions":
            return self.getSessionsForm()
        if id == "accommodation":
            return self.getAccommodationForm()
        if id == "socialEvents":
            return self.getSocialEventForm()
        if id == "furtherInformation":
            return self.getFurtherInformationForm()
        return self.getGeneralSectionFormById(id)

    def _getGeneralSectionGenerator(self):
        try:
            if self._generalSectionGenerator:
                pass
        except AttributeError, e:
            self._generalSectionGenerator = Counter()
        return self._generalSectionGenerator

    def getGeneralSectionForms(self):
        try:
            if self.generalSectionForms:
                pass
        except AttributeError, e:
            self.generalSectionForms={}
        return self.generalSectionForms

    def getGeneralSectionFormById(self, id):
        return self.getGeneralSectionForms().get(id, None)

    def getGeneralSectionFormsList(self):
        return self.getGeneralSectionForms().values()

    def addGeneralSectionForm(self, gsf):
        id = str(self._getGeneralSectionGenerator().newCount())
        while self.getGeneralSectionFormById(id) != None:
            id = str(self._getGeneralSectionGenerator().newCount())
        gsf.setId( id )
        gsf.setTitle(  _("Miscellaneous information %s")%gsf.getId())
        self.generalSectionForms[gsf.getId()]=gsf
        self.addToSortedForms(gsf)
        self.notifyModification()

    def removeGeneralSectionForm(self, gsf):
        if self.hasGeneralSectionForm(gsf):
            del self.generalSectionForms[gsf.getId()]
            self.removeFromSortedForms(gsf)
            self.notifyModification()

    def hasGeneralSectionForm(self, gsf):
        return self.getGeneralSectionForms().has_key(gsf.getId())

    def getSortedForms(self):
        try:
            if self._sortedForms:
                pass
        except AttributeError,e:
            self._sortedForms=[]
            self.addToSortedForms(self.reasonParticipationForm)
            self.addToSortedForms(self.sessionsForm)
            self.addToSortedForms(self.accommodationForm)
            self.addToSortedForms(self.socialEventForm)
            self.addToSortedForms(self.furtherInformation)
            for gs in self.getGeneralSectionFormsList():
                self.addToSortedForms(gs)
        return self._sortedForms

    def addToSortedForms(self, form, i=None):
        if i is None:
            i=len(self.getSortedForms())
        try:
            self.getSortedForms().remove(form)
        except ValueError,e:
            pass
        self.getSortedForms().insert(i, form)
        self.notifyModification()
        return True

    def removeFromSortedForms(self, form):
        try:
            self.getSortedForms().remove(form)
        except ValueError,e:
            return False
        self.notifyModification()
        return True

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the RegistrationForm instance """
        if self.getConference() == None:
            return Locator()
        lconf = self.getConference().getLocator()
        return lconf

    def notifyRegistrantRemoval(self, reg):
        acco = reg.getAccommodation()
        if acco is not None:
            accoType = acco.getAccommodationType()
            if accoType is not None:
                accoType.decreaseNoPlaces()
        for se in reg.getSocialEvents():
            se.delete() # It'll decrease the no of places

    def delete(self):
        self.getSessionsForm().clearSessionList()
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def notifyModification(self):
        self._p_changed=1
        self._conf.notifyModification()

class Notification(Persistent):

    def __init__(self):
        self._toList = PersistentList()
        self._ccList = PersistentList()

    def clone(self):
        n=Notification()
        for t in self.getToList():
            n.addToList(t)
        for c in self.getCCList():
            n.addCCList(c)
        return n

    def getToList(self):
        return self._toList

    def setToList(self, tl):
        self._toList = tl

    def addToList(self, to):
        self._toList.append(to)

    def clearToList(self):
        self._toList = PersistentList()

    def getCCList(self):
        return self._ccList

    def setCCList(self, cl):
        self._ccList = cl

    def addCCList(self, cc):
        self._ccList.append(cc)

    def clearCCList(self):
        self._ccList = PersistentList()

    def _printSessions(self, sessionForm, sessionList):
        text = ""
        if sessionForm.isEnabled():
            if sessionForm.getType() == "2priorities":
                session1 = _("""--_("not selected")--""")
                if len(sessionList)>0:
                    session1 = sessionList[0].getTitle()
                session2 = _("""--_("not selected")--""")
                if len(sessionList)>1:
                    session2 = sessionList[1].getTitle()
                text =  _("""%s:
                        - _("First priority"): %s
                        - _("Other option"): %s
                        """)%(sessionForm.getTitle(), session1, session2)
            else:
                sessionListText=[]
                for s in sessionList:
                    sessionListText.append("\n\t\t\t%s"%s.getTitle())
                text = """%s: %s
                        """%(sessionForm.getTitle(), "".join(sessionListText))
        return text

    def _printAccommodation(self, accommodationForm, accommodation):
        text = ""
        if accommodationForm.isEnabled():
            accoType = _("""--_("not selected")--""")
            if accommodation.getAccommodationType() is not None:
                accoType = accommodation.getAccommodationType().getCaption()
            text = _("""%s:
                        - _("Arrival date"): %s
                        - _("Departure date"): %s
                        - _("Accommodation type"): %s
                    """)%(accommodationForm.getTitle(), \
                            accommodation.getArrivalDate().strftime("%d %B %Y"), \
                            accommodation.getDepartureDate().strftime("%d %B %Y"), \
                            accoType)
        return text

    def _printSocialEvents(self, socialEventForm, socialEvents):
        text = ""
        if socialEventForm.isEnabled():
            se = []
            for item in socialEvents:
                se.append( _("- %s [%s place(s) needed]")%(item.getCaption(), item.getNoPlaces()))
            text = ""
            if se != []:
                text = """%s:
                        %s
                        """%(socialEventForm.getTitle(), "\r\n".join(se) or _("""--_("No social events selected")--"""))
        return text

    def _printReasonParticipation(self, reasonParticipationForm, reasonParticipation):
        text = ""
        if reasonParticipationForm.isEnabled():
            text = """%s: %s
                    """%(reasonParticipationForm.getTitle(), reasonParticipation)
        return text

    def _printMiscellaneousInfo(self, gs, mig):
        text=[]
        if gs.isEnabled():
            if mig is not None:
                noitems=True
                text.append("""%s:\r\n\t\t\t"""%(mig.getTitle()))
                #Mods to support sorting fields
                #for f in gs.getFields():
                for f in gs.getSortedFields():
                    mii=mig.getResponseItemById(f.getId())
                    if mii is not None:
                        noitems=False
                        value=": %s"%mii.getValue()
                        if isinstance(mii.getGeneralField().getInput(), LabelInput) and mii.isBillable():
                            value=": %s %s"%(mii.getPrice(), mii.getCurrency())
                        elif isinstance(mii.getGeneralField().getInput(), LabelInput):
                            value=""
                        text.append("""- %s%s\r\n\t\t\t"""%(mii.getCaption(), value))
                if noitems:
                    text.append("""-- no values --\r\n\t\t\t""")
                text.append("\r\n             ")
        return "".join(text)
    
    def _printAllSections(self, regForm, rp):
        sects = []
        for formSection in regForm.getSortedForms():
            if formSection.getId() == "reasonParticipation":
                sects.append("""
             %s"""%self._printReasonParticipation(formSection, rp.getReasonParticipation()))
            elif formSection.getId() == "sessions":
                sects.append("""
             %s"""%self._printSessions(formSection, rp.getSessionList()))
            elif formSection.getId() == "accommodation":
                sects.append("""
             %s"""%self._printAccommodation(formSection, rp.getAccommodation()))
            elif formSection.getId() == "socialEvents":
                sects.append("""
             %s"""%self._printSocialEvents(formSection, rp.getSocialEvents()))
            elif formSection.getId() == "furtherInformation":
                pass
            else:
                sects.append("""
             %s"""%self._printMiscellaneousInfo(formSection, rp.getMiscellaneousGroupById(formSection.getId())))
        return "".join(sects)

    def _getPDInfoText(self, regForm, rp):
        personalData = regForm.getPersonalData()
        sortedKeys = personalData.getSortedKeys()
        text = ""
        for key in sortedKeys:
            pdfield = personalData.getDataItem(key)
            fieldTitle = pdfield.getName()
            fieldValue = ""
            if key == "title":
                fieldValue = rp.getTitle()
            elif key == "firstName":
                fieldValue = rp.getFirstName()
            elif key == "surname":
                fieldValue = rp.getFamilyName()
            elif key == "position":
                fieldValue = rp.getPosition()
            elif key == "institution":
                fieldValue = rp.getInstitution()
            elif key == "address":
                fieldValue = rp.getAddress()
            elif key == "city":
                fieldValue = rp.getCity()
            elif key == "country":
                fieldValue = rp.getCountry()
            elif key == "phone":
                fieldValue = rp.getPhone()
            elif key == "email":
                fieldValue = rp.getEmail()
            elif key == "fax":
                fieldValue = rp.getFax()
            elif key == "personalHomepage":
                fieldValue = rp.getPersonalHomepage()
            if pdfield.isEnabled():
                text += """
             %s: %s""" % (_(fieldTitle),fieldValue)
        return text

    def sendEmailNewRegistrant(self, regForm, rp):
        fromAddr=regForm.getConference().getSupportEmail(returnNoReply=True)
        url = urlHandlers.UHConferenceDisplay.getURL(regForm.getConference())

#        if rp.getConference().getModPay().isActivated():
        if rp.getConference().hasEnabledSection("epay") and rp.getConference().getModPay().isActivated() and rp.doPay():
            epaymentLink = "If you haven't paid for your registration yet, you can do it at %s" % urlHandlers.UHConfRegistrationFormCreationDone.getURL(rp)
            paymentWarning = ", but please, do not forget to proceed with the payment if you haven't done it yet (see the link at the end of this email)."
        else:
            epaymentLink = ""
            paymentWarning = "."

        subject= _("""New registrant in '%s': %s""")%(strip_ml_tags(regForm.getConference().getTitle()), rp.getFullName())
        body=_("""
             _("Event"): %s
             _("Registrant Id"): %s%s
%s
             """)%(   url,rp.getId(), \
                     self._getPDInfoText(regForm,rp), \
                     self._printAllSections(regForm, rp) )
        # send mail to organisers
        if self.getToList() != [] or self.getCCList() != []:
            bodyOrg = _("""
             There is a new registrant in '%s'. See information below:

                      %s
                      """)%(strip_ml_tags(regForm.getConference().getTitle()), \
                              body)
            maildata = { "fromAddr": fromAddr, "toList": self.getToList(), "ccList": self.getCCList(), "subject": subject, "body": bodyOrg }
            GenericMailer.send(GenericNotification(maildata))
        # send mail to participant
        if rp.getEmail().strip() != "":
            bodyReg = _("""
             Congratulations, your registration to %s was successful%s See your information below:

                      %s
             %s
                      """)% (strip_ml_tags(regForm.getConference().getTitle()),paymentWarning,body,epaymentLink)
            to=rp.getEmail().strip()
            maildata = { "fromAddr": fromAddr, "toList": [to], "subject": subject, "body": bodyReg }
            GenericMailer.send(GenericNotification(maildata))

    def sendEmailNewRegistrantDetailsPay(self, regForm,registrant):
        if not registrant.getConference().getModPay().isEnableSendEmailPaymentDetails():
            return
        fromAddr=registrant.getConference().getSupportEmail(returnNoReply=True)
        date=registrant.getConference().getStartDate()
        getTitle=strip_ml_tags(registrant.getConference().getTitle())
        idRegistrant=registrant.getIdPay()
        detailPayment=registrant.getConference().getModPay().getPaymentDetails()
        subject=_("""New registrant in '%s': %s - payment""")%(strip_ml_tags(registrant.getConference().getTitle()), registrant.getFullName())
        body= _("""
Please use this information for your payment (except for e-payment):\n
- date conference    : %s
- name conference    : %s
- registration id    : %s
- detail of payment  : \n%s
""")%(date,getTitle,idRegistrant,strip_ml_tags(detailPayment))
        booking=[]
        total=0
        booking.append( _("""
detail of Booking:
\tQuantity\t\tItem\t\tunit.price\t\tCost"""))
        for gsf in registrant.getMiscellaneousGroupList():
            miscGroup=registrant.getMiscellaneousGroupById(gsf.getId())
            if miscGroup is not None:
                for miscItem in miscGroup.getResponseItemList():
                    _billlable=False
                    price=0.0
                    quantity=0
                    caption=miscItem.getCaption()
                    currency=miscItem.getCurrency()
                    value=""
                    if miscItem is not None:
                        v=miscItem.getValue()
                        if miscItem.isBillable():
                            _billlable=miscItem.isBillable()
                            value=miscItem.getValue()
                            price=string.atof(miscItem.getPrice())
                            quantity=miscItem.getQuantity()
                            total+=price*quantity
                    if value != "":
                        value=":%s"%value
                    if(quantity>0):
                         booking.append("""%i\t\t%s : %s%s\t\t%s\t\t%s %s"""%(quantity,miscGroup.getTitle(),caption,value,price,price*quantity,currency) )
        booking.append("""\nTOTAL\t\t\t\t\t\t\t%s %s"""%(total,regForm.getCurrency()))
        # send email to organisers
        #if self.getToList() != [] or self.getCCList() != []:
        #    bodyOrg = """
        #     There is a new registrant in '%s'. See information below:
        #
        #              %s
        #              """%(strip_ml_tags(registrant.getConference().getTitle()), \
        #                      body)
        #    maildata = { "fromAddr": fromAddr, "toList": self.getToList(), "ccList": self.getCCList(), "subject": subject, "body": bodyOrg }
        #    GenericMailer.send(GenericNotification(maildata))
        # send email to participants
        if registrant.getEmail().strip() != "":
            bodyReg = _("""
             Please, see the summary of your order:\n\n%s\n\n%s""")%\
                                                                                 ("\n".join(booking),body)
            to=registrant.getEmail().strip()
            maildata = { "fromAddr": fromAddr, "toList": [to], "subject": subject, "body": bodyReg }
            GenericMailer.send(GenericNotification(maildata))

    def sendEmailNewRegistrantConfirmPay(self, regForm,registrant):
        fromAddr=registrant.getConference().getSupportEmail(returnNoReply=True)
        date=registrant.getConference().getStartDate()
        getTitle=strip_ml_tags(registrant.getConference().getTitle())
        idRegistrant=registrant.getIdPay()

        subject= _("""New registrant in '%s': %s""")%(strip_ml_tags(registrant.getConference().getTitle()), registrant.getFullName())
        body= _("""
        thank you for the payment :\n

- detail of payment  : \n%s
- date conference    : %s
- name conference    : %s
- registration id    : %s""")%(registrant.getTransactionInfo().getTransactionTxt(),date,getTitle,idRegistrant)
        booking=[]
        total=0
        booking.append( _(""" Thank you for this payment """))
        booking.append("""Quantity\t\tItem\t\tunit.price\t\tCost""")
        for gsf in registrant.getMiscellaneousGroupList():
            miscGroup=registrant.getMiscellaneousGroupById(gsf.getId())
            if miscGroup is not None:
                for miscItem in miscGroup.getResponseItemList():
                    _billlable=False
                    price=0.0
                    quantity=0
                    caption=miscItem.getCaption()
                    currency=miscItem.getCurrency()
                    v=""
                    if miscItem is not None:
                        v=miscItem.getValue()
                        if miscItem.isBillable():
                            _billlable=miscItem.isBillable()
                            v=miscItem.getValue()
                            price=string.atof(miscItem.getPrice())
                            quantity=miscItem.getQuantity()
                            total+=price*quantity
                    if v != "":
                        v = ":%s"%v
                    if(quantity>0):
                         booking.append("""%i\t\t%s : %s%s\t\t%s\t\t%s %s"""%\
                                        (quantity,gsf.getTitle(),caption,v,price,price*quantity,currency) )
        booking.append("""\nTOTAL\t\t\t\t\t\t\t%s %s"""%(total,regForm.getCurrency()))
        # send email to organisers
        if self.getToList() != [] or self.getCCList() != []:
            bodyOrg =  _("""
             There is a new registrant in '%s'. See information below:

                      %s
                      """)%(strip_ml_tags(registrant.getConference().getTitle()), \
                              body)
            maildata = { "fromAddr": fromAddr, "toList": self.getToList(), "ccList": self.getCCList(), "subject": subject, "body": bodyOrg }
            GenericMailer.send(GenericNotification(maildata))
        # send email to participant
        if registrant.getEmail().strip() != "":
            bodyReg =  _("""
             Congratulations, your registration and your payment were successful. See your informations below:\n\n%s\n\n%s""")%\
                                                                                 ("\n".join(booking),body)
            to=registrant.getEmail().strip()
            maildata = { "fromAddr": fromAddr, "toList": [to], "subject": subject, "body": bodyReg }
            GenericMailer.send(GenericNotification(maildata))

    def sendEmailModificationRegistrant(self, regForm, rp):
        fromAddr=regForm.getConference().getSupportEmail(returnNoReply=True)
        subject= _("""Registration modified for '%s': %s""")%(strip_ml_tags(regForm.getConference().getTitle()), rp.getFullName())
        body= _("""
              _("Registrant Id"): %s
              _("Title"): %s
              _("Family Name"): %s
              _("First Name"): %s
              _("Position"): %s
              _("Institution"): %s
              _("Address"): %s
              _("City"): %s
              _("Country"): %s
              _("Phone"): %s
              _("Fax"): %s
              _("Email"): %s
              _("Personal Homepage"): %s
%s
             """)%(   rp.getId(), \
                     rp.getTitle(), \
                     rp.getFamilyName(), \
                     rp.getFirstName(), \
                     rp.getPosition(), \
                     rp.getInstitution(), \
                     rp.getAddress(), \
                     rp.getCity(), \
                     rp.getCountry(), \
                     rp.getPhone(), \
                     rp.getFax(), \
                     rp.getEmail(), \
                     rp.getPersonalHomepage(), \
                     self._printAllSections(regForm, rp) )
        if self.getToList() != [] or self.getCCList() != []:
            bodyOrg = _("""
             A registrant has modified his/her registration for '%s'. See information below:

                      %s
                      """)%(strip_ml_tags(regForm.getConference().getTitle()), \
                              body)
            maildata = { "fromAddr": fromAddr, "toList": self.getToList(), "ccList": self.getCCList(), "subject": subject, "body": bodyOrg }
            GenericMailer.send(GenericNotification(maildata))

    def exportXml(self, xmlGen):
        """Write xml tags about this object in the given xml generator of type XMLGen."""
        xmlGen.openTag( "notification" )
        xmlGen.writeTag( "toList", ", ".join(self.getToList()) )
        xmlGen.writeTag( "ccList", ", ".join(self.getCCList()) )
        xmlGen.closeTag( "notification" )

class BaseForm(Persistent):

    """
    Base class for registration forms

    It includes iterators/getters, provided if the class attribute
    _iterableContainer is present. _iterableContainer is a simple workaround for
    the problem of having a generic iterator interface over all the forms, even
    if the initial design didn't unify the form container into a BaseForm
    attribute. Since it is too late now for redesigning the DB schema, this
    attribute kind of fixes it.

    """

    # should be overloaded if iteration is to be provided
    _iterableContainer = None

    def __init__(self):
        self._enabled = True # it means that the form cannot be used either in the registration display or in the management area.

    def setEnabled(self, v):
        self._enabled = v

    def isEnabled(self):
        try:
            if self._enabled:
                pass
        except AttributeError, e:
            self._enabled = True
        return self._enabled

    def __iter__(self):
        return getattr(self, self._iterableContainer).__iter__();

    def __getitem__(self, key):
        return getattr(self, self._iterableContainer)[key]


class FieldInputType(Persistent):
    _id=""

    def __init__(self, field):
        self._parent = field

    def getValues(self):
        return {}

    def setValues(self, data):
        pass

    def getParent(self):
        return self._parent

    def setId( cls, id ):
        cls._id=id
    setId = classmethod( setId )

    def getId( cls ):
        return cls._id
    getId = classmethod( getId )

    def getName(cls):
        return cls._id
    getName=classmethod(getName)

    def getHTMLName(self):
        """
        This method returns the indentifier of the field item in the web form.
        """
        return "*genfield*%s-%s"%(self.getParent().getParent().getId(), self.getParent().getId())

    def getModifHTML(self, item, registrant):
        """
        Method that display the form web which represents this object.
        """
        mandatory="<td>&nbsp;&nbsp;</td>"
        if (item is not None and item.isMandatory())or self.getParent().isMandatory():
            mandatory = """<td valign="top"><font color="red">* </font></td>"""
        return "<table><tr>%s%s</tr></table>"%(mandatory, self._getModifHTML(item, registrant))

    def _getModifHTML(self,item, registrant):
        """
        Method that should be overwritten by the classes inheriting from this one in order to display
        the form web which represents this object.
        """
        return ""

    def setResponseValue(self, item, params, registrant, mg=None):
        """
        This method shouldn't be called from the classes inheriting from this one (FieldInputType).
        This method fills the attribute "item" (MiscellaneousInfoSimpleItem) with the value the user wrote
        in the registration form.
        """
        if item is None:
            item=MiscellaneousInfoSimpleItem(mg, self.getParent())
            mg.addResponseItem(item)
        self._setResponseValue(item, params, registrant)

    def _setResponseValue(self, item, registrant, params):
        """
        Method that should be overwritten by the classes inheriting from this one in order to get the value written in the form.
        """
        pass

    def _getSpecialOptionsHTML(self):
        price= self._parent.getPrice()
        billable=self._parent.isBillable()
        checked=""
        if billable:
            checked="checked=\"checked\""

        html= _(""" <tr>
                  <td class="titleCellTD"><span class="titleCellFormat">Is Billable</span></td>
                  <td bgcolor="white" class="blacktext" width="100%%">
                    <input type="checkbox" name="billable" size="60" %s> _("(uncheck if it is not billable)")
                  </td>
                </tr>
                <tr>
                  <td class="titleCellTD"><span class="titleCellFormat"> _("Price")</span></td>
                  <td bgcolor="white" class="blacktext" width="100%%">
                    <input type="text" name="price" size="60" value=%s>
                  </td>
                </tr>
                           """)%(checked,price)
        return "".join(html)

    def clone(self, gf):
        fi=FieldInputs().getAvailableInputKlassById(self.getId())(gf)
        return fi

class TextInput(FieldInputType):
    _id="text"

    def getName(cls):
        return "Text"
    getName=classmethod(getName)

    def _getModifHTML(self,item, registrant):
        caption = self._parent.getCaption()
        price= self._parent.getPrice()
        billable=self._parent.isBillable()
        currency=self._parent.getParent().getRegistrationForm().getCurrency()
        htmlName=self.getHTMLName()
        v=""
        if item is not None:
            v=item.getValue()
            caption = self._parent.getCaption()
            price= item.getPrice()
            billable=item.isBillable()
            currency=item.getCurrency()
            htmlName=item.getHTMLName()
        disable=""
        if ( registrant is not None and billable and registrant.getPayed() ):
            disable="disabled=\"true\""
            #pass
        tmp = """&nbsp;%s <input type="text" name="%s" value="%s" size="60" %s >"""%(caption, htmlName, v ,disable)
        tmp= """ <td>%s</td><td align="right" align="bottom">"""%tmp
        if billable:
            tmp= """%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s</td> """%(tmp,price,currency)
        else:
            tmp= """%s </td> """%tmp
        return tmp

    def _setResponseValue(self, item, params, registrant):
        if ( registrant is not None and self._parent.isBillable() and registrant.getPayed() ):
            #if ( item is not None and item.isBillable()):
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
        v=params.get(self.getHTMLName(),"")
        if self.getParent().isMandatory() and v.strip()=="":
            raise FormValuesError( _("The field \"%s\" is mandatory. Please fill it.")%self.getParent().getCaption())

        item.setQuantity(0)
        item.setValue(v)
        #item.setBillable(self._parent.isBillable())
        #item.setPrice(self._parent.getPrice())
        #item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())
    def _getSpecialOptionsHTML(self):
        return ""

class TextareaInput(FieldInputType):
    _id="textarea"

    def getName(cls):
        return "Textarea"
    getName=classmethod(getName)

    def _getModifHTML(self,item, registrant):
        caption = self._parent.getCaption()
        price= self._parent.getPrice()
        billable=self._parent.isBillable()
        currency=self._parent.getParent().getRegistrationForm().getCurrency()
        htmlName=self.getHTMLName()
        v=""
        if item is not None:
            v=item.getValue()
            caption = self._parent.getCaption()
            price= item.getPrice()
            billable=item.isBillable()
            currency=item.getCurrency()
            htmlName=item.getHTMLName()
        disable=""
        if ( registrant is not None and billable and registrant.getPayed() ):
            disable="disabled=\"true\""
            #pass
        tmp = """&nbsp;%s<br><textarea name="%s" cols="60" rows="4" %s >%s</textarea>"""%(caption, htmlName, disable, v)
        tmp= """ <td>%s</td><td align="right" align="bottom">"""%tmp
        tmp= """%s </td> """%tmp
        return tmp

    def _setResponseValue(self, item, params, registrant):
        if ( registrant is not None and self._parent.isBillable() and registrant.getPayed() ):
            #if ( item is not None and item.isBillable()):
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
        v=params.get(self.getHTMLName(),"")
        if self.getParent().isMandatory() and v.strip()=="":
            raise FormValuesError( _("The field \"%s\" is mandatory. Please fill it.")%self.getParent().getCaption())
        item.setQuantity(0)
        item.setValue(v)
        #item.setBillable(self._parent.isBillable())
        #item.setPrice(self._parent.getPrice())
        #item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())

    def _getSpecialOptionsHTML(self):
        return ""

class NumberInput(FieldInputType):
    _id="number"
    def getName(cls):
        return "Number"
    getName=classmethod(getName)

    def _getModifHTML(self,item, registrant):
        caption = self._parent.getCaption()
        price= self._parent.getPrice()
        billable=self._parent.isBillable()
        currency=self._parent.getParent().getRegistrationForm().getCurrency()
        htmlName=self.getHTMLName()
        v="0"
        if item is not None:
            v=item.getValue()
            caption = self._parent.getCaption()
            price= item.getPrice()
            billable=item.isBillable()
            currency=item.getCurrency()
            htmlName=item.getHTMLName()

        disable=""
        if ( registrant is not None and billable and registrant.getPayed()):
            disable="disabled=\"true\""
            #pass
        tmp = """&nbsp;<input type="text" name="%s" value="%s" %s size="6">&nbsp;&nbsp;%s """%(htmlName, v,disable,caption)
        tmp= """ <td>%s</td><td align="right" align="bottom">"""%tmp
        if billable:
            tmp= """%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s</td> """%(tmp,price,currency)
        else:
            tmp= """%s </td> """%tmp
        return tmp

    def _setResponseValue(self, item, params, registrant):
        v=params.get(self.getHTMLName(),"")
        quantity = 0
        if ( registrant is not None and self._parent.isBillable() and registrant.getPayed()):
            #if ( item is not None and item.isBillable() ):
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
        if self.getParent().isMandatory() and v.strip()=="":
            raise FormValuesError( _("The field \"%s\" is mandatory. Please fill it.")%self.getParent().getCaption())
        if self.getParent().isMandatory() and (not v.isalnum() or int(v)<1):
            raise FormValuesError( _("The field \"%s\" is mandatory. Please fill it with a number.")%self.getParent().getCaption())
        if ( not v.isalnum() or int(v)<1):
            quantity = 0
        else:
            quantity = int(v)
        item.setQuantity(quantity)
        item.setValue(quantity)
        item.setBillable(self._parent.isBillable())
        item.setPrice(self._parent.getPrice())
        item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())

class LabelInput(FieldInputType):
    _id="label"
    def getName(cls):
        return "Label"
    getName=classmethod(getName)

    def _getModifHTML(self,item, registrant):
        caption = self._parent.getCaption()
        price= self._parent.getPrice()
        billable=self._parent.isBillable()
        currency=self._parent.getParent().getRegistrationForm().getCurrency()
        htmlName=self.getHTMLName()
        v=""
        if item is not None:
            v=item.getValue()
            caption = self._parent.getCaption()
            price= item.getPrice()
            billable=item.isBillable()
            currency=item.getCurrency()
            htmlName=item.getHTMLName()

        disable=""
        if ( registrant is not None and billable and registrant.getPayed()):
            disable="disabled=\"true\""
            #pass
        tmp = """&nbsp;%s"""%(caption)
        tmp= """ <td>%s</td><td align="right" align="bottom">"""%tmp
        if billable:
            tmp= """%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s</td> """%(tmp,price,currency)
        else:
            tmp= """%s </td> """%tmp
        return tmp

    def _setResponseValue(self, item, params, registrant):
        if ( registrant is not None and self._parent.isBillable() and registrant.getPayed()):
            #if ( item is not None and item.isBillable()):
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
            #item.setQuantity(0)
        #else:
        item.setQuantity(1)
        item.setValue("")
        item.setBillable(self._parent.isBillable())
        item.setPrice(self._parent.getPrice())
        item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())
        #v=params.get(self.getHTMLName(),"")
        #if self.getParent().isMandatory() and v.strip()=="":
        #    raise FormValuesError("The field \"%s\" is mandatory. Please fill it."%self.getParent().getCaption())
        #item.setValue(v)


class CheckboxInput(FieldInputType):
    _id="checkbox"
    def getName(cls):
        return "Multiple choices/checkbox"
    getName=classmethod(getName)

    def _getModifHTML(self, item,registrant):
        disable=""
        checked=""
        caption = self._parent.getCaption()
        price = self._parent.getPrice()
        billable = self._parent.isBillable()
        currency = self._parent.getParent().getRegistrationForm().getCurrency()
        htmlName = self.getHTMLName()
        v = ""
        if item is not None:
            v = item.getValue()
            caption = self._parent.getCaption()
            price = item.getPrice()
            billable = item.isBillable()
            currency = item.getCurrency()
            htmlName = item.getHTMLName()
        if ( registrant is not None and billable and registrant.getPayed()):
            disable="disabled=\"true\""
            #pass
        if v=="yes":
            checked="checked=\"checked\""
        tmp=  """<input type="checkbox" name="%s" %s %s> %s"""%(htmlName, checked,disable, caption)
        tmp= """ <td>%s</td><td align="right" align="bottom">"""%tmp
        if billable:
            tmp= """%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s</td> """%(tmp, price, currency)
        else:
            tmp= """%s </td> """%tmp
        return tmp

    def _setResponseValue(self, item, params, registrant):
        if (registrant is not None and self._parent.isBillable() and registrant.getPayed()):
            #if ( item is not None and item.isBillable()):
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
        if params.has_key(self.getHTMLName()):
            item.setValue("yes")
            item.setQuantity(1)
        else:
            item.setValue("no")
            item.setQuantity(0)
        item.setBillable(self._parent.isBillable())
        item.setPrice(self._parent.getPrice())
        item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())

class YesNoInput(FieldInputType):
    _id="yes/no"

    def getName(cls):
        return "Yes/No"
    getName=classmethod(getName)

    def _getModifHTML(self,item, registrant):
        caption = self._parent.getCaption()
        price= self._parent.getPrice()
        billable=self._parent.isBillable()
        currency=self._parent.getParent().getRegistrationForm().getCurrency()
        htmlName=self.getHTMLName()
        caption=self._parent.getCaption()
        v="no"
        if item is not None:
            v=item.getValue()
            caption = self._parent.getCaption()
            price= item.getPrice()
            billable=item.isBillable()
            currency=item.getCurrency()
            htmlName=item.getHTMLName()
            caption=item.getCaption()
        disable=""
        checkedYes=""
        checkedNo=""
        if ( registrant is not None and billable and registrant.getPayed()):
            disable="disabled=\"true\""
            #pass
        if v=="yes":
            checkedYes="selected"
        elif v=="no":
            checkedNo="selected"
        tmp=  """&nbsp;%s <select name="%s" %s><option value="yes" %s>yes</option><option value="no" %s>no</option></select>"""%(caption, htmlName,disable, checkedYes, checkedNo)
        tmp= """ <td>%s</td><td align="right" align="bottom">"""%tmp
        if billable:
            tmp= """%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s</td> """%(tmp,price,currency)
        else:
            tmp= """%s </td> """%tmp
        return tmp



    def _setResponseValue(self, item, params, registrant):
        if (registrant is not None and self._parent.isBillable() and registrant.getPayed()):
            #if ( item is not None and item.isBillable()):
            #    return
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
        v=params.get(self.getHTMLName())
        if v=="yes":
            item.setQuantity(1)
        else:
            item.setQuantity(0)
        item.setValue(v)
        item.setBillable(self._parent.isBillable())
        item.setPrice(self._parent.getPrice())
        item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())

class RadioItem(Persistent):

    def __init__(self, parent):
        self._parent=parent
        self._id=""
        self._caption=""
        self._billable=False
        self._price=""
        self._enabled=True

    #def getQuantity(self):return 1
    def getId(self):
        return self._id

    def setId(self, id):
        self._id=id

    def getCaption(self):
        return self._caption

    def setCaption(self, cap):
        self._caption=cap

    def setEnabled(self, en=True):
        self._enabled = en

    def isEnabled(self):
        try:
            return self._enabled
        except:
            self.setEnabled()
            return self._enabled

    def isBillable(self):
        try:
            return self._billable
        except:
            self._billable = False
        return self._billable

    def setBillable(self,v):
        self._billable=v

    def getPrice(self):
        try:
            return self._price
        except:
            self.setPrice(False)
        return self._price

    def setPrice(self,v):
        self._price=v

    def clone(self, parent):
        ri=RadioItem(parent)
        ri.setCaption(self.getCaption())
        ri.setBillable(self.isBillable())
        ri.setPrice(self.getPrice())
        ri.setEnabled(self.isEnabled())
        return ri

    def _cmpCaption(r1, r2):
        return cmp(r1.getCaption(), r2.getCaption())
    _cmpCaption=staticmethod(_cmpCaption)

class RadioGroupInput(FieldInputType):
    _id="radio"
    #def getQuantity(self): return 1
    def getName(cls):
        return "Multiple options/One choice"
    getName=classmethod(getName)

    def __init__(self, field):
        FieldInputType.__init__(self, field)
        self._items={}
        self._radioItemGenerator = Counter()
        self._defaultItem=None

    def getValues(self):
        d={}
        d["radioitems"]=[]
        for i in self._items.values():
            tmp={}
            tmp["caption"]=i.getCaption()
            tmp["billable"]=i.isBillable()
            tmp["price"]=i.getPrice()
            tmp["isEnabled"]=i.isEnabled()
            d["radioitems"].append(tmp)
        d["defaultItem"]=self.getDefaultItem()
        return d

    def setValues(self, data):
        if data.has_key("radioitems"):
            ris=data.get("radioitems",[])
            if type(ris)!=list:
                ris=[ris]
            for c in ris:
                ri=RadioItem(self)
                ri.setCaption(c["caption"])
                ri.setBillable(c["billable"])
                ri.setPrice(c["price"])
                ri.setEnabled(c["isEnabled"])
                self.addItem(ri)
        if data.has_key("defaultItem"):
            self.setDefaultItem(data.get("defaultItem",None))

    def getDefaultItem(self):
        try:
            if self._defaultItem:
                pass
        except AttributeError, e:
            self._defaultItem=None
        return self._defaultItem

    def setDefaultItem(self, caption):
        if self._defaultItem==caption:
            self._defaultItem=None
        else:
            self._defaultItem=caption

    def setDefaultItemById(self, id):
        if self._items.has_key(id):
            self.setDefaultItem(self._items[id].getCaption())

    def getItemsList(self, sort=True):
        vs=self._items.values()
        if sort:
            vs.sort(RadioItem._cmpCaption)
        return vs

    def addItem(self, v):
        v.setId( str(self._getRadioItemGenerator().newCount()) )
        self._items[v.getId()]=v
        self.notifyModification()

    def removeItem(self, v):
        if self._items.has_key(v.getId()):
            del self._items[v.getId()]
            self.notifyModification()

    def removeItemById(self, id):
        if self._items.has_key(id):
            del self._items[id]
            self.notifyModification()

    def disableItemById(self, id):
        if self._items.has_key(id):
            self._items[id].setEnabled(not self._items[id].isEnabled())
            self.notifyModification()

    def getItemById(self, id):
        return self._items.get(id, None)

    def notifyModification(self):
        self._p_changed=1

    def clone(self, gf):
        rgi=FieldInputType.clone(self, gf)
        for item in self.getItemsList():
            rgi.addItem(item.clone(rgi))
        rgi.setDefaultItem(self.getDefaultItem())
        return rgi

    def _getRadioItemGenerator(self):
        return self._radioItemGenerator

    def _getModifHTML(self,item, registrant):

        caption = self._parent.getCaption()
        price= self._parent.getCaption()
        billable=self._parent.isBillable()
        currency=self._parent.getParent().getRegistrationForm().getCurrency()
        value = ""
        if item is not None:
            price = item.getPrice()
            billable = item.isBillable()
            currency = item.getCurrency()
            caption = item.getCaption()
            value = item.getValue()
        tmp = """&nbsp;%s """%(caption)
        tmp= [""" <td>%s</td><td align="right" align="bottom">"""%tmp]
        tmp.append(""" </td> """)
        for val in self.getItemsList():
            disable=""
            if not val.isEnabled():
                disable="disabled=\"true\""
            if ( registrant is not None and (val.isBillable() or billable) and registrant.getPayed()):
                disable="disabled=\"true\""
                #pass
            checked=""
            if val.getCaption()==value:
                checked="checked"
            elif not value and val.getCaption() == self.getDefaultItem():
                checked="checked"
            tmp.append("""<tr><td></td><td><input type="radio" name="%s"  value="%s" %s %s> %s</td><td align="right" align="bottom">"""%(self.getHTMLName(), val.getId(), checked,disable, val.getCaption()))
            if val.isBillable():
                tmp.append("""&nbsp;&nbsp;%s&nbsp;&nbsp;%s</td></tr> """%(val.getPrice(),currency))
            else:
                 tmp.append(""" </td></tr> """)

        return "".join(tmp)



    def _setResponseValue(self, item, params, registrant):
        v=params.get(self.getHTMLName(),"")
        billable=False
        for val in self._items.values():
            if val.isBillable():
                billable = True
        if ( registrant is not None and self._parent.isBillable() and registrant.getPayed() ):
            #if (item is not None and billable):
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
        if self.getParent().isMandatory() and v.strip()=="":
            raise FormValuesError( _("The field \"%s\" is mandatory. Please fill it.")%self.getParent().getCaption())
        price=0
        quantity=0
        caption = ""
        if v.strip() != "":
            radioitemid=params.get(self.getHTMLName())
            radioitem=self.getItemById(radioitemid)
            caption=radioitem.getCaption()
            billable=radioitem.isBillable()
            price=radioitem.getPrice()
            quantity=1
        item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setValue(caption)
        item.setBillable(billable)
        item.setPrice(price)
        item.setQuantity(quantity)


    def _getSpecialOptionsHTML(self):
        html=["""<tr>
          <td class="titleCellTD"><span class="titleCellFormat">Radio items</span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
                <table>"""]
        html.append( _("""<tr>
                            <td valign="top" align="left">
                            <table>
                            <tr>
                                <td class="blacktext"><span class="titleCellFormat"> _("Caption")</span></td>
                                <td bgcolor="white" class="blacktext" width="100%%">
                                    <input type="text" name="newradioitem">
                                </td>
                            </tr>
                            <tr>
                                <td class="blacktext"><span class="titleCellFormat"> _("Billable")</span></td>
                                <td bgcolor="white" class="blacktext" width="100%%">
                                    <input type="checkbox" name="newbillable" >
                                </td>
                            </tr>
                            <tr>
                                <td class="blacktext"><span class="titleCellFormat"> _("Price")</span></td>
                                <td bgcolor="white" class="blacktext" width="100%%">
                                    <input type="text" name="newprice">
                                </td>
                           </tr>
                            </table>
                            </td>
                            <td rowspan="2" valign="top" align="left">
                                <input type="submit" class="btn" name="addradioitem" value="_("add")" onFocus="javascript: addIsFocused = true;" onBlur="javascript: addIsFocused = false;"><br>
                                <input type="submit" class="btn" name="removeradioitem" value="_("remove")"><br>
                                <input type="submit" class="btn" name="disableradioitem" value="_("enable/disable")"><br>
                                <input type="submit" class="btn" name="defaultradioitem" value="_("set as default")"><br>
                            </td>
                        </tr>
                """))
        html.append("""<tr><td valign="top" align="left"><table>""")
        billable = False
        for v in self.getItemsList(True):
            html.append("""
                        <tr>
                            <td bgcolor="white" class="blacktext" ><input type="checkbox" name="radioitems" value="%s">%s</td>
                            <td bgcolor="white" class="blacktext" >
                        """%(v.getId(), v.getCaption()))
            if v.isBillable():
                billable = True
                html.append( _("""<span class="titleCellFormat">&nbsp;&nbsp; _("Price"):%s</span>""")%(v.getPrice()))
            if not v.isEnabled():
                html.append("""<span><font color="red">&nbsp;&nbsp;(""" + _("disabled") + """)</font></span>""")
            if v.getCaption()==self.getDefaultItem():
                html.append("""<span><font color="green">&nbsp;&nbsp;(""" + _("default") + """)</font></span>""")
            html.append("""
                             </td>
                        </tr>
                      """)
        html.append("""</table></td></tr>""")
        if billable:
            html.append("""<input type="hidden" name="billable" value="">""")
        html.append("""</table></td></tr>""")
        return "".join(html)


class FieldInputs:

    _availableInputs={TextInput.getId():TextInput, \
                      TextareaInput.getId(): TextareaInput, \
                      LabelInput.getId():LabelInput, \
                      NumberInput.getId():NumberInput, \
                      RadioGroupInput.getId():RadioGroupInput, \
                      CheckboxInput.getId():CheckboxInput, \
                      YesNoInput.getId(): YesNoInput }

    def getAvailableInputs(cls):
        return cls._availableInputs
    getAvailableInputs=classmethod(getAvailableInputs)

    def getAvailableInputKlassById(cls,id):
        return cls._availableInputs.get(id, None)
    getAvailableInputKlassById=classmethod(getAvailableInputKlassById)

    def getAvailableInputKeys(cls):
        return cls._availableInputs.keys()
    getAvailableInputKeys=classmethod(getAvailableInputKeys)

class GeneralField(Persistent):

    def __init__(self, parent, data=None):
        self._parent=parent
        self._id = ""
        if data is None:
            self._caption = "General Field"
            self._input = FieldInputs.getAvailableInputKlassById("text")(self)
            self._input.setValues(data)
            self._mandatory = False
            self._billable =False
            self._price = "0"
        else:
            self.setValues(data)

    def clone(self, newsection):
        field = GeneralField(newsection, self.getValues())
        return field

    def setValues(self, data):
        caption=data.get("caption","")
        if caption=="":
            caption= _("General Field")
        self.setCaption(caption)
        self.setInput(FieldInputs.getAvailableInputKlassById(data.get("input","text"))(self))
        self._input.setValues(data)
        self.setMandatory(data.has_key("mandatory"))
        self.setBillable(data.has_key("billable"))
        self.setPrice(data.get("price",""))

    def getValues(self):
        values = {}
        values["caption"] = self.getCaption()
        values["input"] = self.getInput().getId()
        values["mandatory"] = self.isMandatory()
        values["billable"]=self.isBillable()
        values["price"]=self.getPrice()
        return values

    def isBillable(self):
        try:
            return self._billable
        except:
            self._billable = False
        return self._billable

    def setBillable(self,v):
        self._billable=v

    def getPrice(self):
        try:
            return self._price
        except:
            self._price = 0
        return self._price

    def setPrice(self,price):
        self._price=price

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getCaption(self):
        return self._caption

    def setCaption(self, caption):
        self._caption = caption

    def getInput(self):
        return self._input

    def setInput(self, input):
        self._input = input

    def isMandatory(self):
        return self._mandatory

    def setMandatory(self, v):
        self._mandatory = v

    def getParent(self):
        return self._parent

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the GeneralField instance """
        if self.getParent() == None:
            return Locator()
        lconf = self.getParent().getLocator()
        lconf["sectionFieldId"] = self.getId()
        return lconf

class GeneralSectionForm(BaseForm):

    def __init__(self, regForm, data=None):
        BaseForm.__init__(self)
        self._regForm=regForm
        self._id=""
        self._title = _("Miscellaneous information")
        self._description = ""

        #####
        #Mods to support sorting fields
        #self._fields=[]

        self._sortedFields=[]

        if data is not None:
            self._title = data.get("title", self._title)
            self._description = data.get("description", self._description)
        self._generalFieldGenerator = Counter()

    def setValues(self, data):
        title=data.get("title","").strip()
        if title=="":
            title= _("Miscellaneous information %s")%self.getId()
        self.setTitle(title)
        self.setDescription(data.get("description", ""))

    def getValues(self):
        values = {}
        values["title"] = self.getTitle()
        values["description"] = self.getDescription()
        values["enabled"] = self.isEnabled()
        return values

    def clone(self, regForm):
        gsf = GeneralSectionForm(regForm)
        gsf.setId(self.getId())
        gsf.setValues(self.getValues())
        gsf.setEnabled(self.isEnabled())

        #Mods to support sorting fields
        #for field in self.getFields():
        for field in self.getSortedFields():
            gsf.addToSortedFields(field.clone(gsf))
        return gsf

    def getRegistrationForm(self):
        return self._regForm

    def getConference(self):
        return self._regForm.getConference()

    def _getGeneralFieldGenerator(self):
        return self._generalFieldGenerator

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getTitle(self):
        return self._title

    def setTitle(self, title):
        self._title = title

    def getDescription(self):
        return self._description

    def setDescription(self, n):
        self._description = n

    ###########
    #Mods to support sorting fields
    #def getFields(self):
    #    return self._fields
    #
    #def addField(self, f):
    #    if f not in self.getFields():
    #        f.setId( str(self._getGeneralFieldGenerator().newCount()) )
    #        self.getFields().append(f)
    #        self.notifyModification()
    #
    #def removeField(self, f):
    #    if f in self.getFields():
    #        self.getFields().remove(f)
    #        self.notifyModification()
    #
    #def getFieldById(self, id):
    #    for f in self.getFields():
    #            if f.getId()==id:
    #                return f
    #        return None

    def getSortedFields(self):
        try:
           returnFields = self._sortedFields
        except AttributeError:
           self._sortedFields = self._fields
           returnFields = self._sortedFields
        return returnFields


    def addToSortedFields(self, f, i=None):
        if i is None:
            i=len(self.getSortedFields())
        try:
            self.getSortedFields().remove(f)
        except ValueError,e:
            pass
        f.setId( str(self._getGeneralFieldGenerator().newCount()) )
        self.getSortedFields().insert(i, f)
        self.notifyModification()
        return True

    def removeField(self, f):
        if f in self.getSortedFields():
            self.getSortedFields().remove(f)
            self.notifyModification()

    def getFieldById(self, id):
        for f in self.getSortedFields():
            if f.getId()==id:
               return f
        return None
    #
    #end mods
    ##########

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the GeneralSectionForm instance """
        if self.getRegistrationForm().getConference() == None:
            return Locator()
        lconf = self.getRegistrationForm().getLocator()
        lconf["sectionFormId"] = self.getId()
        return lconf

    def notifyModification(self):
        self._p_changed=1

class PersonalDataFormItem(Persistent):

    def __init__(self, data=None):
        if data is None:
            self._id = ""
            self._name = ""
            self._input = ""
            self._mandatory = False
            self._enabled = True
        else:
            self._id = data.get("id","")
            self._name = data.get("name","")
            self._input = data.get("input","")
            self._mandatory = data.get("mandatory",False)
            self._enabled = data.get("enabled",True)

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getName(self):
        return self._name

    def setName(self, name):
        self._name = name

    def isEnabled(self):
        try:
            return self._enabled
        except:
            self.setEnabled()
            return self._enabled

    def setEnabled(self, enabled=True):
        self._enabled = enabled
        self._p_changed = 1

    def getInput(self):
        return self._input

    def setInput(self, input):
        self._input = input

    def isMandatory(self):
        return self._mandatory

    def setMandatory(self, v):
        self._mandatory = v
        self._p_changed = 1

class PersonalData(Persistent):

    def __init__(self):
        self._initStandardPersonalData()

    def _initStandardPersonalData(self):
        self._data = PersistentMapping()
        self._sortedKeys = PersistentList()
        p = PersonalDataFormItem({'id':'title', 'name': _("Title"), 'input':'list', 'mandatory':False})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'firstName', 'name': _("First Name"), 'input':'text', 'mandatory':True})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'surname', 'name': _("Surname"), 'input':'text', 'mandatory':True})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'position', 'name': _("Position"), 'input':'text', 'mandatory':False})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'institution', 'name': _("Institution"), 'input':'text', 'mandatory':True})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'address', 'name': _("Address"), 'input':'text', 'mandatory':False})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'city', 'name': _("City"), 'input':'text', 'mandatory':True})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'country', 'name': _("Country"), 'input':'list', 'mandatory':True})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'phone', 'name': _("Phone"), 'input':'text', 'mandatory':False})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'fax', 'name': _("Fax"), 'input':'text', 'mandatory':False})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'email', 'name': _("Email"), 'input':'hidden', 'mandatory':True})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'personalHomepage', 'name': _("Personal homepage"), 'input':'text', 'mandatory':False})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())

    def getValuesFromAvatar(self, av):
        r = {}
        r["title"] = ""
        r["firstName"] = ""
        r["surname"] = ""
        r["institution"] = ""
        r["email"] = ""
        r["address"] = ""
        r["phone"] = ""
        r["fax"] = ""
        if av is not None:
            r["title"] = av.getTitle()
            r["firstName"] = av.getFirstName()
            r["surname"] = av.getFamilyName()
            r["institution"] = av.getOrganisation()
            r["email"] = av.getEmail()
            r["address"] = av.getAddress()
            r["phone"] = av.getTelephone()
            faxes = av.getFaxes()
            fax = ""
            if len(faxes)>0:
                fax = faxes[0]
            r["fax"] = fax
        return r

    def getValuesFromRegistrant(self, reg):
        r = {}
        r["title"] = reg.getTitle()
        r["firstName"] = reg.getFirstName()
        r["surname"] = reg.getFamilyName()
        r["position"] = reg.getPosition()
        r["institution"] = reg.getInstitution()
        r["address"] = reg.getAddress()
        r["city"] = reg.getCity()
        r["country"] = reg.getCountry()
        r["phone"] = reg.getPhone()
        r["fax"] = reg.getFax()
        r["email"] = reg.getEmail()
        r["personalHomepage"] = reg.getPersonalHomepage()

        return r

    def getData(self):
        return self._data

    def getSortedKeys(self):
        return self._sortedKeys

    def getMandatoryItems(self):
        r = []
        for i in self.getSortedKeys():
            if self.getData()[i].isMandatory() and self.getData()[i].isEnabled():
                r.append(i)
        return r

    def getDataItem(self, key):
        return self._data.get(key, None)


class FurtherInformationForm(BaseForm):

    def __init__(self, data=None):
        BaseForm.__init__(self)
        self._title = _("Further information")
        self._content = ""
        if data is not None:
            self._title = data.get("title", self._title)
            self._content = data.get("content", self._content)
        self._id="furtherInformation"

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="furtherInformation"
        return self._id

    def setValues(self, data):
        self.setTitle(data.get("title", _("Further Information")))
        self.setContent(data.get("content", ""))

    def getValues(self):
        values = {}
        values["title"] = self.getTitle()
        values["content"] = self.getContent()
        values["enabled"] = self.isEnabled()
        return values

    def clone(self):
        fif = FurtherInformationForm()
        fif.setValues(self.getValues())
        fif.setEnabled(self.isEnabled())
        return fif

    def getTitle(self):
        return self._title

    def setTitle(self, title):
        self._title = title

    def getContent(self):
        return self._content

    def setContent(self, n):
        self._content = n

class AccommodationType(Persistent):

    def __init__(self, rf, data=None):
        self._id=""
        self._caption=""
        self._regForm = rf
        self._cancelled = False
        self._placesLimit = 0
        self._currentNoPlaces = 0

    def setValues(self, data):
        self.setCaption(data.get("caption", "--no caption--"))
        self.setCancelled(data.has_key("cancelled"))
        self.setPlacesLimit(data.get("placesLimit", "0"))
        self._regForm.notifyModification()

    def getValues(self):
        values = {}
        values["caption"] = self.getCaption()
        if self.isCancelled():
            values["cancelled"] = self.isCancelled()
        values["placesLimit"] = self.getPlacesLimit()

        return values

    def clone(self, registrationForm):
        act = AccommodationType(registrationForm)
        act.setValues(self.getValues())
        return act

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getCaption(self):
        return self._caption

    def setCaption(self, c):
        self._caption = c

    def getPlacesLimit(self):
        try:
            if self._placesLimit:
                pass
        except AttributeError, e:
            self._placesLimit = 0
        return self._placesLimit

    def setPlacesLimit(self, limit):
        if limit=="":
            limit="0"
        try:
            l = int(limit)
        except ValueError, e:
            raise FormValuesError( _("Please introduce a number for the limit of places"))
        self._placesLimit = l
        self.updateCurrentNoPlaces()

    def getCurrentNoPlaces(self):
        try:
            if self._currentNoPlaces:
                pass
        except AttributeError, e:
            self._currentNoPlaces = 0
        return self._currentNoPlaces

    def hasAvailablePlaces(self):
        if self.getCurrentNoPlaces() >= self.getPlacesLimit():
            return False
        return True

    def getNoPlacesLeft(self):
        return self.getPlacesLimit() - self.getCurrentNoPlaces()

    def increaseNoPlaces(self):
        if self.getPlacesLimit() > 0 :
            if self.getCurrentNoPlaces() >= self.getPlacesLimit():
                raise FormValuesError( _("""The limit for the number of places is smaller than the current amount registered for this accommodation. Please, set a higher limit."""))
            self._currentNoPlaces += 1

    def decreaseNoPlaces(self):
        if self.getPlacesLimit() > 0 and self.getCurrentNoPlaces() > 0:
            self._currentNoPlaces -= 1

    def updateCurrentNoPlaces(self):
        self._currentNoPlaces = 0
        for reg in self._regForm.getConference().getRegistrantsList():
            acco = reg.getAccommodation()
            if acco is not None:
                accoType = acco.getAccommodationType()
                if accoType is not None and accoType == self:
                    self.increaseNoPlaces()

    def getRegistrationForm(self):
        return self._regForm

    def setRegistrationForm(self, rf):
        self._regForm = rf

    def isCancelled(self):
        try:
            if self._cancelled:
                pass
        except AttributeError, e:
            self._cancelled = False
        return self._cancelled

    def setCancelled(self, v):
        self._cancelled = v

    def remove(self):
        self.setCancelled(True)
        self.delete()

    def delete(self):
        self.setRegistrationForm(None)
        TrashCanManager().add(self)
    def recover(self, rf):
        self.setRegistrationForm(rf)
        TrashCanManager().remove(self)

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the AccommodationType instance """
        if self.getRegistrationForm().getConference() == None:
            return Locator()
        lconf = self.getRegistrationForm().getLocator()
        lconf["accoTypeId"] = self.getId()
        return lconf

class AccommodationForm(BaseForm):

    _iterableContainer = '_accommodationTypes'

    def __init__(self, regForm, data=None):
        BaseForm.__init__(self)
        self._accoTypeGenerator = Counter()
        self._regForm = regForm
        self._title = _("Accommodation")
        self._description = ""
        self._currency = "CHF"
        self._accommodationTypes = PersistentMapping()
        if data is not None:
            self._title = data.get("title", self._title)
            self._description = data.get("description", self._description)
            self._currency = data.get("currency", self._currency)
        self._setDefaultAccommodationTypes()
        self._id="accommodation"
        self._arrivalOffsetDates=[-2,0]
        self._departureOffsetDates=[1,3]

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="accommodation"
        return self._id

    def getConference(self):
        return self._regForm.getConference()

    def getArrivalOffsetDates( self ):
        try:
            return self._arrivalOffsetDates
        except:
            self.setDefaultArrivalOffsetDates()
            return self._arrivalOffsetDates

    def setDefaultArrivalOffsetDates(self):
        self._arrivalOffsetDates = [-2,0]

    def getArrivalDates(self):
        offsets = self.getArrivalOffsetDates()
        conf = self.getConference()
        dates = []
        curDate = startDate = conf.getStartDate()+timedelta(days=offsets[0])
        endDate = conf.getEndDate()+timedelta(days=offsets[1])
        if startDate > endDate:
            endDate = startDate
        while curDate <= endDate:
            dates.append(curDate)
            curDate += timedelta(days=1)
        return dates

    def setArrivalOffsetDates(self, dates):
        self._arrivalOffsetDates = dates

    def getDepartureOffsetDates( self ):
        try:
            return self._departureOffsetDates
        except:
            self.setDefaultDepartureOffsetDates()
            return self._departureOffsetDates

    def setDefaultDepartureOffsetDates(self):
        self._departureOffsetDates = [1,3]

    def getDepartureDates(self):
        offsets = self.getDepartureOffsetDates()
        conf = self.getConference()
        dates = []
        curDate = startDate = conf.getStartDate()+timedelta(days=offsets[0])
        endDate = conf.getEndDate()+timedelta(days=offsets[1])
        if startDate > endDate:
            endDate = startDate
        while curDate <= endDate:
            dates.append(curDate)
            curDate += timedelta(days=1)
        return dates

    def setDepartureOffsetDates(self, dates):
        self._departureOffsetDates = dates

    def _setDefaultAccommodationTypes(self):
        a = AccommodationType(self._regForm)
        a.setId("cern")
        a.setCaption( _("CERN Hostel"))
        self._accommodationTypes[a.getId()] = a
        a = AccommodationType(self._regForm)
        a.setId("own-accommodation")
        a.setCaption( _("I will arrange my own accommodation"))
        self._accommodationTypes[a.getId()] = a
        a = AccommodationType(self._regForm)
        a.setId("geneva-hotel")
        a.setCaption( _("I prefer to book a room in a Geneva hotel"))
        self._accommodationTypes[a.getId()] = a

    def setValues(self, data):
        self.setTitle(data.get("title", "Sessions"))
        self.setDescription(data.get("description", ""))
        self.setCurrency(data.get("currency", ""))
        self.setArrivalOffsetDates([int(data.get("aoffset1",-2)),int(data.get("aoffset2",0))])
        self.setDepartureOffsetDates([int(data.get("doffset1",1)),int(data.get("doffset2",3))])

    def getValues(self):
        values = {}
        values["title"] = self.getTitle()
        values["description"] = self.getDescription()
        values["currency"] = self.getCurrency()
        values["enabled"] = self.isEnabled()
        values["aoffset1"] = self.getArrivalOffsetDates()[0]
        values["aoffset2"] = self.getArrivalOffsetDates()[1]
        values["doffset1"] = self.getDepartureOffsetDates()[0]
        values["doffset2"] = self.getDepartureOffsetDates()[1]
        return values

    def clone(self, registrationForm):
        acf = AccommodationForm(registrationForm)
        acf.setValues(self.getValues())
        acf.setEnabled(self.isEnabled())
        acf._accommodationTypes = PersistentMapping()
        for at in self.getAccommodationTypesList() :
            acf.addAccommodationType(at.clone(registrationForm))
        return acf

    def getTitle(self):
        return self._title

    def setTitle(self, title):
        self._title = title

    def getDescription(self):
        return self._description

    def setDescription(self, description):
        self._description = description

    def getCurrency(self):
        return self._currency

    def setCurrency(self, currency):
        self._currency = currency

    def getRegistrationForm(self):
        return self._regForm

    def _generateNewAccoTypeId( self ):
        """Returns a new unique identifier for the current registration form
        """
        try:
            return str(self._accoTypeGenerator.newCount())
        except:
            self._accoTypeGenerator = Counter()
            return str(self._accoTypeGenerator.newCount())

    def addAccommodationType(self, accom):
        id = accom.getId()
        if id == "":
            id = self._generateNewAccoTypeId()
            accom.setId(id)
        self._accommodationTypes[id] = accom

    def removeAccommodationType(self, accom):
        accom.remove()
        if self._accommodationTypes.has_key(accom.getId().strip()):
            del(self._accommodationTypes[accom.getId().strip()])

    def recoverAccommodationType(self, accom):
        self.addAccommodationType(accom)
        accom.recover(self.getRegistrationForm())

    def getAccommodationTypeById(self, id):
        if self._accommodationTypes.has_key(id.strip()):
            return self._accommodationTypes[id]
        return None

    def getAccommodationTypesList(self):
        return self._accommodationTypes.values()

    def clearAccommodationTypesList(self):
        for at in self.getAccommodationTypesList():
            self.removeAccommodationType(at)


class ReasonParticipationForm(BaseForm):

    def __init__(self, data=None):
        BaseForm.__init__(self)
        self._title = _("Reason for participation")
        self._description = _("Please, let us know why you are interested on participate in our event:")
        if data is not None:
            self._title = data.get("title", self._title)
            self._description = data.get("description",self._description)
        self._id="reasonParticipation"

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="reasonParticipation"
        return self._id

    def setValues(self, data):
        self.setTitle(data.get("title", _("Reason for participation")))
        self.setDescription(data.get("description", ""))

    def getValues(self):
        values = {}
        values["title"] = self.getTitle()
        values["description"] = self.getDescription()
        return values

    def clone(self):
        rpf = ReasonParticipationForm()
        rpf.setValues(self.getValues())
        rpf.setEnabled(self.isEnabled())
        return rpf

    def getTitle(self):
        return self._title

    def setTitle(self, title):
        self._title = title

    def getDescription(self):
        return self._description

    def setDescription(self, description):
        self._description = description

class SessionItem(Persistent):

    def __init__(self, rf, data=None):
        self._session = None
        self._regForm = rf
        self._cancelled = False

    def getRegistrationForm(self):
        return self._regForm

    def setRegistrationForm(self, rf):
        self._regForm = rf

    def isCancelled(self):
        try:
            if self._cancelled:
                pass
        except AttributeError, e:
            self._cancelled = False
        return self._cancelled

    def setCancelled(self, v):
        self._cancelled = v

    def remove(self):
        self.setCancelled(True)

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the SocialEventItem instance """
        if self.getRegistrationForm().getConference() == None:
            return Locator()
        lconf = self.getRegistrationForm().getLocator()
        lconf["sessionItemId"] = self.getId()
        return lconf

class RegistrationSession(Persistent):

    def __init__(self, ses, regForm=None):
        self._session = ses
        self._session.setRegistrationSession(self)
        self._regForm = regForm

    def getSession(self):
        return self._session

    def setSession(self, ses):
        self._session = ses

    def getRegistrationForm(self):
        return self._regForm

    def setRegistrationForm(self, rf):
        self._regForm = rf

    def getParent(self):
        # The parent of registration session is "session form"
        if self._regForm is not None:
            return self._regForm.getSessionsForm()
        return None

    def getConference(self):
        if self._regForm is not None:
            return self._regForm.getConference()
        return None

    def remove(self):
        #self._session.setRegistrationSession(None)
        self.setRegistrationForm(None)
        pass

    def isCancelled(self):
##        return self._session is None or not self.getParent().hasSession(self.getId())
##        return not self.getParent().hasSession(self.getId())
        return not self.getRegistrationForm()

    def getId(self):
        return self._session.getId()

    def getTitle(self):
        return self._session.getTitle()

    # for compatibility with other fields
    getCaption = getTitle

    def getStartDate(self):
        return self._session.getStartDate()

    def getCode(self):
        return self._session.getCode()

    def _cmpTitle(s1, s2):
        if s1 is None and s2 is not None:
            return -1
        elif s1 is not None and s2 is None:
            return 1
        elif s1 is None and s2 is None:
            return 0
        return cmp(s1.getTitle(), s2.getTitle())
    _cmpTitle=staticmethod(_cmpTitle)

class SessionsForm(BaseForm):

    _iterableContainer = '_sessions'

    def __init__(self, data=None):
        BaseForm.__init__(self)
        self._title = "Sessions"
        self._type = "2priorities"
        self._description = ""
        self._sessions = PersistentMapping()
        if data is not None:
            self._title = data.get("title", self._title)
            self._description = data.get("description", self._description)
            self._sessions = data.get("sessions", self._sessions)
        self._id="sessions"

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="sessions"
        return self._id

    def clone(self, newSessions):
        sesf = SessionsForm()
        sesf.setTitle(self.getTitle())
        sesf.setType(self.getType())
        sesf.setDescription(self.getDescription())
        sesf.setEnabled(self.isEnabled())
        #TODO: Cloning of registrant session
        #for s in newSessions :
        #    sesf.addSession(s)

        return sesf

    def setValues(self, data):
        self.setTitle(data.get("title", "Sessions"))
        self.setDescription(data.get("description", ""))
        self.setType(data.get("sessionFormType", "2priorities"))

    def getTitle(self):
        return self._title

    def setTitle(self, title):
        self._title = title

    def getDescription(self):
        return self._description

    def setDescription(self, description):
        self._description = description

    def getType(self):
        try:
            if self._type:
                pass
        except AttributeError, e:
            self._type = "2priorities"
        return self._type

    def setType(self, type):
        self._type = type

    def getSessionsFromParams(self, params):
        sessions = []
        if self.isEnabled():
            if self.getType() == "2priorities":
                if params.get("session1", "nosession") == "nosession":
                    raise FormValuesError( _("Please, choose at least one session in order to register"))
                if params.get("session1", "") == params.get("session2", "nosession"):
                    raise FormValuesError( _("You cannot choose the same session twice"))
                sessions.append(self.getSessionById(params.get("session1")))
                ses2 = self.getSessionById(params.get("session2", "nosession"))
                if ses2 is not None:
                    sessions.append(ses2)
            elif self.getType() == "all":
                sess=params.get("sessions", [])
                if type(sess) != list:
                    sess=[sess]
                for ses in sess:
                    sessions.append(self.getSessionById(ses))
        return sessions

    def getSessionList(self, doSort=False):
        lv = self._sessions.values()
        lv.sort(sortByStartDate)
        if doSort:
            lv.sort(RegistrationSession._cmpTitle)
        return lv

    def addSession(self, ses):
        if not self._sessions.has_key(ses.getId()):
            self._sessions[ses.getId()] = ses

    def removeSession(self, sesId):
        if self._sessions.has_key(sesId):
            self._sessions[sesId].remove()
            del self._sessions[sesId]

    def clearSessionList(self):
        for s in self.getSessionList():
            self.removeSession(s)

    def hasSession(self, key):
        return self._sessions.has_key(key)

    def getSessionById(self, id):
        return self._sessions.get(id, None)


def sortByStartDate( x, y ):
    return cmp(x.getSession().getStartDate(),y.getSession().getStartDate())


class SocialEventItem(Persistent):

    def __init__(self, rf, data=None):
        self._id=""
        self._caption=""
        self._regForm = rf
        self._cancelled = False
        self._cancelledReason = ""
        self._maxPlacePerRegistrant = 9
        self._placesLimit = 0
        self._currentNoPlaces = 0

    def setValues(self, data):
        self.setCaption(data.get("caption", "--no caption--"))
        self.setCancelled(data.has_key("cancelled"))
        self.setCancelledReason(data.get("reason", ""))
        self.setMaxPlacePerRegistrant(int(data.get("maxPlace", "10")))
        self.setPlacesLimit(data.get("placesLimit", "0"))

    def getValues(self):
        data={}
        data["caption"]=self.getCaption()
        if self.isCancelled():
            data["cancelled"]=self.isCancelled()
        data["reason"]=self.getCancelledReason()
        data["maxPlace"]=self.getMaxPlacePerRegistrant()
        data["placesLimit"]=self.getPlacesLimit()
        return data

    def clone(self, regForm):
        newSEI=SocialEventItem(regForm)
        newSEI.setValues(self.getValues())
        return newSEI

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getCaption(self):
        return self._caption

    def setCaption(self, c):
        self._caption = c

    def getPlacesLimit(self):
        try:
            if self._placesLimit:
                pass
        except AttributeError, e:
            self._placesLimit = 0
        return self._placesLimit

    def setPlacesLimit(self, limit):
        if limit=="":
            limit="0"
        try:
            l = int(limit)
        except ValueError, e:
            raise FormValuesError( _("Please introduce a number for the limit of places"))
        self._placesLimit = l
        self.updateCurrentNoPlaces()

    def getCurrentNoPlaces(self):
        try:
            if self._currentNoPlaces:
                pass
        except AttributeError, e:
            self._currentNoPlaces = 0
        return self._currentNoPlaces

    def hasAvailablePlaces(self):
        if self.getCurrentNoPlaces() >= self.getPlacesLimit():
            return False
        return True

    def getNoPlacesLeft(self):
        return self.getPlacesLimit() - self.getCurrentNoPlaces()

    def increaseNoPlaces(self, n):
        if self.getPlacesLimit() > 0 :
            if (self.getCurrentNoPlaces()+n) > self.getPlacesLimit():
                raise FormValuesError( _("We are sorry but there are not enough places for the social event \"%s\". \
                         ")%(self.getCaption()))
            self._currentNoPlaces += n

    def decreaseNoPlaces(self, n):
        if self.getPlacesLimit() > 0 and self.getCurrentNoPlaces() > 0:
            if (self._currentNoPlaces - n)<0:
                raise FormValuesError( _("Impossible to decrease %s places for \"%s\" because the current number of \
                        places would be less than zero")%(n, self.getCaption()))
            self._currentNoPlaces -= n

    def updateCurrentNoPlaces(self):
        self._currentNoPlaces = 0
        for reg in self._regForm.getConference().getRegistrantsList():
            for se in reg.getSocialEvents():
                if se.getSocialEventItem() == self:
                    self.increaseNoPlaces(se.getNoPlaces())

    def getRegistrationForm(self):
        return self._regForm

    def setRegistrationForm(self, rf):
        self._regForm = rf

    def isCancelled(self):
        try:
            if self._cancelled:
                pass
        except AttributeError, e:
            self._cancelled = False
        return self._cancelled

    def setCancelled(self, v):
        self._cancelled = v

    def getCancelledReason(self):
        try:
            if self._cancelledReason:
                pass
        except AttributeError:
            self._cancelledReason = ""
        return self._cancelledReason

    def setCancelledReason(self, cr):
        self._cancelledReason = cr

    def getMaxPlacePerRegistrant(self):
        try:
            return self._maxPlacePerRegistrant
        except AttributeError:
            self._maxPlacePerRegistrant = 9
        return self._maxPlacePerRegistrant

    def setMaxPlacePerRegistrant(self, numPlace):
        self._maxPlacePerRegistrant = numPlace

    def remove(self):
        self.setCancelled(True)
        self.delete()

    def delete(self):
        self.setRegistrationForm(None)
        TrashCanManager().add(self)

    def recover(self, rf):
        self.setRegistrationForm(rf)
        TrashCanManager().remove(self)

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the SocialEventItem instance """
        if self.getRegistrationForm().getConference() == None:
            return Locator()
        lconf = self.getRegistrationForm().getLocator()
        lconf["socialEventId"] = self.getId()
        return lconf

    def _cmpCaption(se1, se2):
        return cmp(se1.getCaption().lower(), se2.getCaption().lower())

class SocialEventForm(BaseForm):

    _iterableContainer = '_socialEvents'

    def __init__(self, regForm, data=None):
        BaseForm.__init__(self)
        self._socialEventItemGenerator = Counter()
        self._regForm = regForm
        self._title = _("Social Events")
        self._description = ""
        self._introSentence=self._getDefaultIntroValue()
        self._selectionType="multiple"
        self._socialEvents = PersistentMapping()
        if data is not None:
            self._title = data.get("title", self._title)
            self._description = data.get("description", self._description)
        self._id="socialEvents"

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="socialEvents"
        return self._id

    def setValues(self, data):
        self.setTitle(data.get("title", _("Sessions")))
        self.setDescription(data.get("description", ""))
        self.setIntroSentence(data.get("intro", ""))
        self.setSelectionType(data.get("selectionType","multiple"))

    def getValues(self):
        values = {}
        values["title"] = self.getTitle()
        values["description"] = self.getDescription()
        values["intro"] = self.getIntroSentence()
        values["selectionType"] = self.getSelectionTypeId()
        return values

    def clone(self, registrationForm):
        sef = SocialEventForm(registrationForm)
        sef.setValues(self.getValues())
        sef.setEnabled(self.isEnabled())

        for se in self.getSocialEventList() :
            sef.addSocialEvent(se.clone(registrationForm))
        return sef

    def getTitle(self):
        return self._title

    def setTitle(self, title):
        self._title = title

    def getDescription(self):
        return self._description

    def setDescription(self, description):
        self._description = description

    def getRegistrationForm(self):
        try:
            if self._regForm:
                pass
        except AttributeError, e:
            self._regForm=None
        return self._regForm

    def getConference(self):
        if self.getRegistrationForm() is not None:
            return self.getRegistrationForm().getConference()
        return None

    def _getDefaultIntroValue(self):
        return _("""<b> _("Select the social events you would like to attend and how many places you will need"):</b>""")

    def getIntroSentence(self):
        try:
            if self._introSentence:
                pass
        except AttributeError, e:
            self._introSentence=self._getDefaultIntroValue()
        return self._introSentence

    def setIntroSentence(self, intro):
        self._introSentence=intro

    def getSelectionTypeList(self):
        try:
            if self._selectionTypeList:
                pass
        except AttributeError, e:
            self._selectionTypeList={"multiple": "Multiple choice",
                                     "unique": "Unique choice"}
        return self._selectionTypeList

    def _getSelectionType(self):
        try:
            if self._selectionType:
                pass
        except AttributeError, e:
            self._selectionType="multiple"
        return self._selectionType

    def getSelectionTypeId(self):
        return self._getSelectionType()

    def getSelectionTypeCaption(self):
        return self.getSelectionTypeList()[self._getSelectionType()]

    def setSelectionType(self, id):
        self._selectionType=id

    def _generateNewSocialEventItemId( self ):
        """Returns a new unique identifier for the current registration form
        """
        try:
            return str(self._socialEventItemGenerator.newCount())
        except:
            self._socialEventItemGenerator = Counter()
            return str(self._socialEventItemGenerator.newCount())

    def addSocialEvent(self, se):
        id = se.getId()
        if id == "":
            id = self._generateNewSocialEventItemId()
            se.setId(id)
        self._socialEvents[id] = se

    def removeSocialEvent(self, se):
        se.remove()
        if self._socialEvents.has_key(se.getId().strip()):
            del(self._socialEvents[se.getId().strip()])

    def recoverSocialEvent(self, se):
        self.addSocialEvent(se)
        se.recover(self.getRegistrationForm())

    def getSocialEventById(self, id):
        if self._socialEvents.has_key(id.strip()):
            return self._socialEvents[id]
        return None

    def getSocialEventList(self, sort=False):
        v=self._socialEvents.values()
        if sort:
            v.sort(SocialEventItem._cmpCaption)
        return v

    def clearSocialEventList(self):
        for se in self.getSocialEventList():
            self.removeSocialEvent(se)

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the GeneralField instance """
        if self.getConference() == None:
            return Locator()
        lconf = self.getConference().getLocator()
        lconf["sectionFieldId"] = self.getId()
        return lconf

class StatusValue(Persistent):

    def __init__(self, st, data=None):
        self._status=st
        self._id=""
        self._caption=""
        if data is not None:
            self.setValues(data)

    def getValues(self):
        d={}
        d["caption"]=self.getCaption()
        return d

    def setValues(self, d):
        self.setCaption(d.get("caption", "-- no caption --"))

    def getId(self):
        return self._id

    def setId(self, id):
        self._id=id

    def getCaption(self):
        return self._caption

    def setCaption(self, cp):
        self._caption=cp

    def clone(self, st):
        sv=StatusValue(st)
        sv.setCaption(self.getCaption())
        return sv

    def _cmpCaption(sv1, sv2):
        return cmp(sv1.getCaption().strip().lower(), sv2.getCaption().strip().lower())
    _cmpCaption=staticmethod(_cmpCaption)


class Status(Persistent):

    def __init__(self, regForm, data=None):
        self._regForm=regForm
        self._statusValues={}
        self._valuesGenerator=Counter()
        self._id=""
        self._caption=""
        self._defaultValue=None
        if data is not None:
            self.setValues(data)
        self.addStatusValue(StatusValue(self, {"caption":"Yes"}))
        self.addStatusValue(StatusValue(self, {"caption":"No"}))

    def setValues(self, d):
        self.setCaption(d.get("caption",""))
        ids=[]
        defaultValueSet=False
        if d.has_key("values") and type(d.get("values",[])) == list:
            for vd in d.get("values",[]):
                id=vd.get("id","")
                if self.getStatusValueById(id) is not None:
                    v=self.getStatusValueById(id)
                    v.setValues(vd)
                else:
                    v=StatusValue(self, vd)
                    self.addStatusValue(v)
                if d.get("defaultvalue","").strip() == id:
                    defaultValueSet=True
                    self.setDefaultValue(v)
                ids.append(v.getId())
        if not defaultValueSet:
            self.setDefaultValue(None)
        for v in self.getStatusValuesList()[:]:
            if v.getId() not in ids:
                self.removeStatusValue(v)


    def getValues(self):
        d={}
        d["caption"]=self.getCaption()
        return d

    def getConference(self):
        return self._regForm.getConference()

    def getId(self):
        return self._id

    def setId(self, i):
        self._id=i

    def getCaption(self):
        return self._caption

    def setCaption(self,c):
        self._caption=c

    def setDefaultValue(self, stval):
        self._defaultValue=stval

    def getDefaultValue(self):
        return self._defaultValue

    def _generateValueId( self ):
        """Returns a new unique identifier for the current registration form
        """
        try:
            return str(self._valuesGenerator.newCount())
        except:
            self._valuesGenerator = Counter()
            return str(self._valuesGenerator.newCount())

    def getStatusValues(self):
        return self._statusValues

    def getStatusValuesList(self, sort=False):
        r=self._statusValues.values()
        if sort:
            r.sort(StatusValue._cmpCaption)
        return r

    def hasStatusValue(self, v):
        if v is not None and self.getStatusValues().has_key(v.getId()):
            return True
        return False

    def getStatusValueById(self, id):
        if self.getStatusValues().has_key(id):
            return self.getStatusValues()[id]
        return None

    def addStatusValue(self, v):
        v.setId(self._generateValueId())
        self.getStatusValues()[v.getId()]=v
        self.notifyModification()

    def removeStatusValue(self, v):
        if self.getStatusValues().has_key(v.getId()):
            del self.getStatusValues()[v.getId()]
            self.notifyModification()

    def _cmpCaption(s1, s2):
        return cmp(s1.getCaption().lower().strip(), s2.getCaption().lower().strip())
    _cmpCaption=staticmethod(_cmpCaption)

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the Status instance """
        if self.getConference() == None:
            return Locator()
        lconf = self.getConference().getLocator()
        lconf["statusId"] = self.getId()
        return lconf

    def notifyModification( self):
        """Method called to notify that the registration form has been modified.
        """
        self._p_changed=1


# Users --------- FINAL INFORMATION STORED FROM THE REGISTRATION FORM

class Registrant(Persistent):

    def __init__(self):
        self._conf = None
        self._avatar = None
        self._id = ""
        self._complete = False
        self._registrationDate = nowutc()

        self._title = ""
        self._firstName = ""
        self._surname = ""
        self._position = ""
        self._institution = ""
        self._address = ""
        self._city = ""
        self._country = ""
        self._phone = ""
        self._fax = ""
        self._email = ""
        self._personalHomepage = ""

        self._sessions = []
        self._socialEvents = []
        self._accommodation = Accommodation()
        self._reasonParticipation = ""

        self._miscellaneous={}
        self._parmasReturn={}
        self._statuses={}
        self._total=0
        self._hasPay=False
        self._transactionInfo=None


        self._randomId = self._generateRandomId()

    def isPayedText(self):
        if self.getPayed() :
            return "Yes"
        elif not self.doPay():
            return "-"
        return "No"

    def getIdPay(self):
        return "c%sr%s"%(self._conf.getId(),self.getId())

    def setTotal(self,total):
        self._total=total

    def getTotal(self):
        try:
            return self._total
        except:
            self.setTotal(0)
        return self._total

    def updateTotal(self):
        total = 0
        for gs in self.getRegistrationForm().getGeneralSectionFormsList():
            if gs.isEnabled():
                mg=self.getMiscellaneousGroupById(gs.getId())
                if mg != None:
                    for miscItem in mg.getResponseItemList():
                        if miscItem.isBillable():
                            price = float(miscItem.getPrice() or 0)
                        else:
                            price = 0
                        quantity = miscItem.getQuantity()
                        total += price*quantity
        self.setTotal(total)

    def doPay(self):
        return self.getTotal()>0 and not self.getPayed()

    def setPersonalData(self, data):
        self.setTitle(data.get("title",""))
        self.setFirstName(data.get("firstName",""))
        self.setSurName(data.get("surname",""))
        self.setPosition(data.get("position",""))
        self.setInstitution(data.get("institution",""))
        self.setAddress(data.get("address",""))
        self.setCity(data.get("city",""))
        self.setCountry(data.get("country",""))
        self.setPhone(data.get("phone",""))
        self.setFax(data.get("fax",""))
        self.setEmail(data.get("email",""))
        self.setPersonalHomepage(data.get("personalHomepage",""))

    def setValues(self, data, av):
        self._avatar = av

        self.setPersonalData(data)

        if self.getRegistrationForm().getReasonParticipationForm().isEnabled():
            self.setReasonParticipation(data.get("reason",""))

        if self.getRegistrationForm().getSessionsForm().isEnabled():
            sessions=data.get("sessions",[])
            if not isinstance(sessions, list):
                sessions = [ sessions ]
            self.setSessions(sessions)

        if self.getRegistrationForm().getAccommodationForm().isEnabled():
            ad = data.get("arrivalDate",None)
            dd = data.get("departureDate",None)
            if ad == "nodate":
                raise FormValuesError( _("Arrival date cannot be empty."))
            elif dd == "nodate":
                raise FormValuesError( _("Departure date cannot be empty."))
            if ad is not None and dd is not None:
                ad = stringToDate(ad)
                dd = stringToDate(dd)
                if ad > dd:
                    raise FormValuesError( _("Arrival date has to be earlier than departure date"))
            if self.getRegistrationForm().getAccommodationForm().getAccommodationTypesList() !=[] and data.get("accommodationType",None) is None:
                raise FormValuesError( _("It is mandatory to choose an accommodation in order to register"))
            self._accommodation.setArrivalDate(ad)
            self._accommodation.setDepartureDate(dd)
            accoType = data.get("accommodationType",None)
            if accoType != None and accoType.isCancelled():
                accoType = None
            if self.getRegistrationForm().getAccommodationForm().getAccommodationTypesList() !=[]:
                self._accommodation.setAccommodationType(accoType)

        if self.getRegistrationForm().getSocialEventForm().isEnabled():
            for seItem in self.getSocialEvents()[:]:
                self.removeSocialEventById(seItem.getId())
            for seItem in data.get("socialEvents", []):
                newSE = SocialEvent(seItem, int(data.get("places-%s"%seItem.getId(), "1")))
                self.addSocialEvent(newSE)
        #if not self.getPayed():
        #    self._miscellaneous = {}
        total = 0
        for gs in self.getRegistrationForm().getGeneralSectionFormsList():
            if gs.isEnabled():
                mg=self.getMiscellaneousGroupById(gs.getId())
                if mg==None:
                    mg=MiscellaneousInfoGroup(self, gs)
                    self.addMiscellaneousGroup(mg)
                #Mods to support sorting fields
                #for f in gs.getFields():
                for f in gs.getSortedFields():
                    f.getInput().setResponseValue(mg.getResponseItemById(f.getId()),data, self, mg)
                for miscItem in mg.getResponseItemList():
                    if miscItem.isBillable():
                        price = float(miscItem.getPrice() or 0)
                    else:
                        price = 0
                    quantity = miscItem.getQuantity()
                    total += price*quantity
        if not self.getPayed():
            self.setTotal(total)
        self._complete = True

    def isComplete(self):
        try:
            if self._complete:
                pass
        except AttributeError, e:
            self._complete = False
        return self._complete

    def getPayed(self):
        try:
            return self._hasPay
        except:
            self.setPayed(False)
        return self._hasPay

    def setPayed(self,hasPay):
        self._hasPay=hasPay

    def getTransactionInfo(self):
        try:
            return self._transactionInfo
        except:
            self.setTransactionInfo(False)
        return self._transactionInfo

    def setTransactionInfo(self,transactionInfo):
        self._transactionInfo=transactionInfo

    def _generateRandomId(self):
        n=datetime.now()
        return md5.new(str(random.random()+time.mktime(n.timetuple()))).hexdigest()

    def getRandomId(self):
        try:
            if self._randomId:
                pass
        except AttributeError,e:
            self._randomId = self._generateRandomId()
        return self._randomId

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = str(id).strip()

    def getConference(self):
        return self._conf

    def setConference(self, c):
        self._conf = c

    def getOwner(self):
        return self.getConference()

    def setOwner(self, o):
        self.setConference(o)

    def getAvatar(self):
        return self._avatar

    def setAvatar(self, a):
        if isinstance(self._avatar,MaKaC.user.Avatar):
            self._avatar.unlinkTo(self, "registrant")
        self._avatar = a
        a.linkTo(self, "registrant")

    def getRegistrationForm(self):
        return self.getConference().getRegistrationForm()

    def getRegistrationDate(self):
        try:
            if self._registrationDate:
                pass
        except AttributeError, e:
            self._registrationDate = None
        return self._registrationDate

    def getAdjustedRegistrationDate(self,tz=None):
        if not tz:
            tz = self.getConference().getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        return self.getRegistrationDate().astimezone(timezone(tz))

    def getTitle(self):
        return self._title

    def setTitle(self, v):
        self._title = v

    def getFirstName(self):
        return self._firstName

    def setFirstName(self, v):
        self._firstName = v

    def getSurName(self):
        return self._surname
    getFamilyName = getSurName

    def setSurName(self, v):
        self._surname = v
    setFamilyName = setSurName

    def getFullName( self, title=True, firstNameFirst=False ):
        if firstNameFirst:
            res = "%s %s"%( self.getFirstName(), self.getFamilyName())
            res = res.strip()
        else:
            res = self.getFamilyName().upper()
            if self.getFirstName() != "":
                res = "%s, %s"%( res, self.getFirstName() )
        if title and self.getTitle() != "":
            res = "%s %s"%( self.getTitle(), res )
        return res

    def getPosition(self):
        return self._position

    def setPosition(self, v):
        self._position = v

    def getInstitution(self):
        return self._institution

    def setInstitution(self, v):
        self._institution = v

    def getAddress(self):
        return self._address

    def setAddress(self, v):
        self._address = v

    def getCity(self):
        return self._city

    def setCity(self, v):
        self._city = v

    def getCountry(self):
        return self._country

    def setCountry(self, v):
        self._country = v

    def getPhone(self):
        return self._phone

    def setPhone(self, v):
        self._phone = v

    def getFax(self):
        return self._fax

    def setFax(self, v):
        self._fax = v

    def getEmail(self):
        return self._email

    def setEmail(self, v):
        self._email = v

    def getPersonalHomepage(self):
        return self._personalHomepage

    def setPersonalHomepage(self, v):
        self._personalHomepage = v

    def getSessionList(self):
        return self._sessions

    def addSession(self, ses):
        self._sessions.append(ses)
        self.notifyModification()

    def removeSession(self, ses):
        self._sessions.remove(ses)
        self.notifyModification()

    def setSessions(self, sesList):
        self._sessions = sesList
        self.notifyModification()

    def setAccommodation(self, a):
        self._accommodation = a

    def getAccommodation(self):
        return self._accommodation

    def setReasonParticipation(self, a):
        self._reasonParticipation = a

    def getReasonParticipation(self):
        return self._reasonParticipation

    def getSocialEvents(self):
        try:
            if self._socialEvents:
                pass
        except AttributeError, e:
            self._socialEvents = []
        return self._socialEvents

    def getSocialEventById(self, id):
        for se in self.getSocialEvents():
            if id == se.getId():
                return se
        return None

    def setSocialEvents(self, se):
        self._socialEvents = se
        self.notifyModification()

    def addSocialEvent(self, se):
        self.getSocialEvents().append(se)
        self.notifyModification()

    def removeSocialEventById(self, id):
        se=self.getSocialEventById(id)
        se.delete()
        self.getSocialEvents().remove(se)
        self.notifyModification()

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the registrant instance """
        if self.getConference() == None:
            return Locator()
        lconf = self.getConference().getLocator()
        lconf["registrantId"] = self.getId()
        return lconf

    def notifyModification( self ):
        """Method called to notify the current registered participant has been modified.
        """
        self._p_changed=1

    def _cmpFamilyName(r1, r2):
        if r1 is None and r2 is None:
            return 0
        if r1 is None:
            return -1
        if r2 is None:
            return 1
        return cmp(r1.getFamilyName().lower(), r2.getFamilyName().lower())
    _cmpFamilyName=staticmethod(_cmpFamilyName)

    def getMiscellaneousGroups(self):
        try:
            if self._miscellaneous:
                pass
        except AttributeError, e:
            self._miscellaneous={}
        return self._miscellaneous

    def getMiscellaneousGroupList(self):
        return self.getMiscellaneousGroups().values()

    def getMiscellaneousGroupById(self, id):
        if self.getMiscellaneousGroups().has_key(id):
            return self.getMiscellaneousGroups()[id]
        return None

    def addMiscellaneousGroup(self, g):
        if not self.getMiscellaneousGroups().has_key(g.getId()):
            self.getMiscellaneousGroups()[g.getId()]=g
            self.notifyModification()

    def getStatuses(self):
        try:
            if self._statuses:
                pass
        except AttributeError, e:
            self._statuses={}
        return self._statuses

    def getStatusesList(self):
        return self.getStatuses().values()

    def addStatus(self, s):
        self.getStatuses()[s.getId()]=s
        self.notifyModification()

    def removeStatus(self, s):
        if self.getStatuses().has_key(s.getId()):
           del self.getStatuses()[s.getId()]
           self.notifyModification()

    def getStatusById(self, id):
        v=self.getStatuses().get(id, None)
        if v is None:
            st=self._conf.getRegistrationForm().getStatusById(id)
            v=RegistrantStatus(self, st)
            if st.getDefaultValue() is not None:
                v.setStatusValue(st.getDefaultValue())
            self.addStatus(v)
        return v

class Accommodation(Persistent):

    def __init__(self):
        self._arrivalDate = None
        self._departureDate = None
        self._accommodationType = None

    def getArrivalDate(self):
        return self._arrivalDate

    def setArrivalDate(self, ad):
        self._arrivalDate = ad

    def getDepartureDate(self):
        return self._departureDate

    def setDepartureDate(self, dd):
        self._departureDate = dd

    def getAccommodationType(self):
        return self._accommodationType

    def setAccommodationType(self, at):
        if self.getAccommodationType() != at:
            if self.getAccommodationType() is not None:
                self.getAccommodationType().decreaseNoPlaces()
            if at is not None:
                at.increaseNoPlaces()
            self._accommodationType = at

class SocialEvent(Persistent):

    def __init__(self, se, noPlaces):
        self.addSEItem(se, noPlaces)

    def addSEItem(self, se, noPlaces):
        self._socialEventItem = se
        self._noPlaces = noPlaces
        self._socialEventItem.increaseNoPlaces(noPlaces)

    def getNoPlaces(self):
        return self._noPlaces

    def getSocialEventItem(self):
        return self._socialEventItem

    def getId(self):
        return self._socialEventItem.getId()

    def isCancelled(self):
        return self._socialEventItem.isCancelled()

    def getCancelledReason(self):
        return self._socialEventItem.getCancelledReason()

    def getCaption(self):
        return self._socialEventItem.getCaption()

    def getMaxPlacePerRegistrant(self):
        return self._socialEventItem.getMaxPlacePerRegistrant()

    def delete(self):
        self._socialEventItem.decreaseNoPlaces(self._noPlaces)

class MiscellaneousInfoGroup(Persistent):

    def __init__(self, reg, gs):
        self._registrant=reg
        self._generalSection=gs
        self._id=gs.getId()
        self._responseItems={}

    def getId(self):
        return self._id

    def getGeneralSection(self):
        return self._generalSection

    def getTitle(self):
        return self.getGeneralSection().getTitle()

    def getRegistrant(self):
        return self._registrant

    def getResponseItems(self):
        return self._responseItems

    def getResponseItemList(self):
        return self._responseItems.values()

    def addResponseItem(self, r):
        self._responseItems[r.getId()]=r
        self.notifyModification()

    def removeResponseItem(self, i):
        if self.getResponseItems().has_key(i.getId()):
            del self._responseItems[i.getId()]
            self.notifyModification()

    def getResponseItemById(self, id):
        if self._responseItems.has_key(id):
            return self._responseItems[id]
        return None

    def clearResponses(self, gs=None):
        if gs is None:
            self._responseItems={}
            self.notifyModification()
        else:
            #Mods to support sorting fields
            #for f in gs.getFields():
            for f in gs.getSortedFields():
                self.removeResponseItem(f)

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the MiscellaneousInfoGroup instance """
        lconf = self.getRegistrant().getLocator()
        lconf["miscInfoId"] = self.getId()
        return lconf

    def notifyModification(self):
        self._p_changed=1


class MiscellaneousInfoSimpleItem(Persistent):

    def __init__(self, group, field):
        self._group = group
        self._generalField=field
        self._id=field.getId()
        self._value=None
        self._billable=False
        self._price=0.0
        self._quantity=0
        self._currency=""
        self._mandatory=False
        self._HTMLName=""

    def getHTMLName(self):
        try:
            return self._HTMLName
        except:
            self._HTMLName=""
        return self._HTMLName

    def setHTMLName(self,HTMLName):
        self._HTMLName= HTMLName

    def isMandatory(self):
        try:
            return self._mandatory
        except:
            self._mandatory=False
        return self._mandatory

    def setMandatory(self,mandatory):
        self._mandatory= mandatory

    def getCurrency(self):
        try:
            return self._currency
        except:
            self.setCurrency("")
        return self._currency

    def setCurrency(self,currency):
        self._currency= currency

    def getQuantity(self):
        try:
            return self._quantity
        except:
            self.setQuantity(0)
        return self._quantity
    def setQuantity(self,quantity):
        self._quantity= quantity
    def isBillable(self):
        try:
            return self._billable
        except:
            self.setBillable(False)
        return self._billable

    def setBillable(self,v):
        self._billable=v

    def getPrice(self):
        try:
            return self._price
        except:
            self.setPrice(0)
        return self._price

    def setPrice(self,price):
        self._price=price

    def getId(self):
        return self._id

    def getGeneralField(self):
        return self._generalField

    def getCaption(self):
        return self._generalField.getCaption()

    def getOwner(self):
        return self._group
    getGroup=getOwner

    def getValue(self):
        return self._value

    def setValue(self, v):
        self._value = v

class RegistrantStatus(Persistent):

    def __init__(self, reg, st, data=None):
        self._status=st
        self._registrant=reg
        self._value=None
        if data is not None:
            self.setValues()

    def setValues(self, d):
        self.setStatusValue(d.get("statusvalue",""))

    def getValues(self):
        d={}
        d["statusvalue"]=self.getStatusValue()
        return d

    def getId(self):
        return self._status.getId()

    def getCaption(self):
        return self._status.getCaption()

    def getStatusValue(self):
        if not self._status.hasStatusValue(self._value):
            self._value=self._status.getDefaultValue()
        return self._value

    def setStatusValue(self, v):
        self._value=v
