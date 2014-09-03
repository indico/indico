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
from flask import request

import random, time
from uuid import uuid4
from hashlib import md5
from datetime import datetime, timedelta

from pytz import timezone
from pytz import all_timezones
from MaKaC.common.timezoneUtils import nowutc
from persistent import Persistent
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList
import MaKaC
from indico.core.db import eticket
from MaKaC.common.Counter import Counter
from MaKaC.errors import FormValuesError, MaKaCError
from MaKaC.common.Locators import Locator
from indico.core.config import Config
from MaKaC.common.TemplateExec import inlineContextHelp
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.webinterface.common.tools import strip_ml_tags
from MaKaC.trashCan import TrashCanManager
from MaKaC.webinterface.mail import GenericMailer, GenericNotification
from MaKaC.i18n import _
from indico.util.i18n import i18nformat
from indico.util.date_time import format_datetime, format_date
from indico.util.string import safe_upper
from MaKaC.webinterface.common.countries import CountryHolder
import re
import tempfile, os
import string
from MaKaC.webinterface.common.person_titles import TitlesRegistry

from indico.util.fossilize import Fossilizable, fossilizes
from indico.core.fossils.registration import IRegFormTextInputFieldFossil, IRegFormTelephoneInputFieldFossil, \
    IRegFormTextareaInputFieldFossil, IRegFormNumberInputFieldFossil, IRegFormLabelInputFieldFossil, \
    IRegFormCheckboxInputFieldFossil, IRegFormYesNoInputFieldFossil, IRegFormFileInputFieldFossil, \
    IRegFormRadioItemFossil, IRegFormRadioGroupInputFieldFossil, IRegFormCountryInputFieldFossil, \
    IRegFormDateInputFieldFossil, IRegFormGeneralFieldFossil, IRegFormGeneralSectionFossil, \
    IRegFormFurtherInformationSectionFossil, IRegFormAccommodationTypeItemFossil, IRegFormAccommodationSectionFossil, \
    IRegFormReasonParticipationSectionFossil, IRegFormRegistrationSessionItemFossil, IRegFormSessionSectionFossil, \
    IRegFormSocialEventItemFossil, IRegFormSocialEventSectionFossil, IRegFormRegistrantFossil, \
    IRegFormRegistrantBasicFossil, IRegFormRegistrantFullFossil, IRegFormSocialEventFossil, IRegFormMiscellaneousInfoGroupFossil

PRICE_PATTERN = re.compile(r'^(\d+(?:[\.,]\d+)?)$')


def stringToDate(str):
    months = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
              "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}
    [day, month, year] = str.split("-")
    return datetime(int(year), months[month], int(day))


class RegistrationForm(Persistent):

    def __init__(self, conf, groupData=None, skipPersonalData=False):
        self._conf = conf
        if groupData is None:
            self.activated = False
            self.title = "Registration Form"
            self.announcement = ""
            self.usersLimit = 0
            self.contactInfo = ""
            self.setStartRegistrationDate(nowutc())
            self.setEndRegistrationDate(nowutc())
            self.setModificationEndDate(None)
            self.setCurrency("not selected")
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
            self._endExtraTimeAmount = 0
            self._endExtraTimeUnit = 'days'
            self.modificationEndDate = groupData.get("modificationEndDate", None)
            #if self.modificationEndDate is None:
            #    self.setModificationEndDate(nowutc())
            self.contactInfo = groupData.get("contactInfo", "")
            self.setCurrency(groupData.get("Currency", ""))
        self.notification = Notification()
        self._eTicket = eticket.ETicket()
        # Status definition
        self._statuses = {}
        self._statusesGenerator = Counter()
        #Multiple-Subforms
        if not skipPersonalData:
            self.personalData = PersonalDataForm(self)
        #Simple-SubForms
        self.sessionsForm = SessionsForm()
        self.accommodationForm = AccommodationForm(self)
        self.reasonParticipationForm = ReasonParticipationForm()
        self.furtherInformation = FurtherInformationForm()
        self.socialEventForm = SocialEventForm(self)
        #General-SubForms
        self._generalSectionGenerator = Counter()
        self.generalSectionForms = {}
        if not skipPersonalData:
            self.addGeneralSectionForm(self.personalData, True)
        #All SortedForms
        self._sortedForms = []
        if not skipPersonalData:
            self.addToSortedForms(self.personalData)
        self.addToSortedForms(self.reasonParticipationForm)
        self.addToSortedForms(self.sessionsForm)
        self.addToSortedForms(self.accommodationForm)
        self.addToSortedForms(self.socialEventForm)
        self.addToSortedForms(self.furtherInformation)

        self.setAllSessions()

    def clone(self, conference):
        form = RegistrationForm(conference, skipPersonalData=True)
        form.setConference(conference)
        form.setAnnouncement(self.getAnnouncement())
        form.setContactInfo(self.getContactInfo())
        form.setCurrency(self.getCurrency())
        registrationPeriodEnd = self.getConference().getStartDate() - self.getEndRegistrationDate()
        registrationPeriodStart = self.getConference().getStartDate() - self.getStartRegistrationDate()
        form.setEndRegistrationDate(conference.getStartDate() - registrationPeriodEnd)
        form.setEndExtraTimeAmount(self.getEndExtraTimeAmount())
        form.setEndExtraTimeUnit(self.getEndExtraTimeUnit())
        form.setStartRegistrationDate(conference.getStartDate() - registrationPeriodStart)
        if self.getModificationEndDate():
            registrationPeriodModifEndDate = self.getConference().getStartDate() - self.getModificationEndDate()
            form.setModificationEndDate(conference.getStartDate() - registrationPeriodModifEndDate)
        form.setTitle(self.getTitle())
        form.setUsersLimit(self.getUsersLimit())
        form.setActivated(self.isActivated())
        form.setMandatoryAccount(self.isMandatoryAccount())
        form.setNotificationSender(self.getNotificationSender())
        form.setSendRegEmail(self.isSendRegEmail())
        form.setSendReceiptEmail(self.isSendReceiptEmail())
        form.setSendPaidEmail(self.isSendPaidEmail())
        form.setAllSessions()
        form.notification = self.getNotification().clone()
        form._eTicket = self.getETicket().clone()
        form.personalData = self.getPersonalData().clone(form)
        form.generalSectionForms[form.personalData.getId()] = form.personalData
        acf = self.getAccommodationForm()
        if acf is not None:
            form.accommodationForm = acf.clone(form)
        fif = self.getFurtherInformationForm()
        if fif is not None:
            form.furtherInformation = fif.clone()
        rpf = self.getReasonParticipationForm()
        if rpf is not None:
            form.reasonParticipationForm = rpf.clone()
        form.setAllSessions()
        ses = self.getSessionsForm()
        if ses is not None:
            form.sessionsForm = ses.clone(form.sessionsForm.getSessionList())
        sef = self.getSocialEventForm()
        if sef is not None:
            form.socialEventForm = sef.clone(form)
        form._sortedForms = []
        for item in self.getSortedForms():
            clonedItem = form.getSectionById(item.getId())
            if clonedItem is None:  # General Section, not cloned yet
                clonedItem = item.clone(form)
                form.generalSectionForms[clonedItem.getId()] = clonedItem
            form.addToSortedForms(clonedItem)

        return form

    def getCurrency(self):
        try:
            return self._currency
        except:
            self.setCurrency("not selected")
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

    def setNotificationSender(self, sender):
        self._notificationSender = sender

    def getNotificationSender(self):
        sender = None
        try:
            if self._notificationSender:
                sender = self._notificationSender
        except AttributeError, e:
            pass
        if not sender:
            self._notificationSender = self._conf.getSupportInfo().getEmail(returnNoReply=True).split(',', 1)[0]
        return self._notificationSender

    def isSendRegEmail(self):
        try:
            if self._sendRegEmail:
                pass
        except AttributeError, e:
            self._sendRegEmail = True
        return self._sendRegEmail

    def setSendRegEmail(self, v=True):
        self._sendRegEmail = v

    def isSendReceiptEmail(self):
        try:
            if self._sendReceiptEmail:
                pass
        except AttributeError, e:
            self._sendReceiptEmail = False
        return self._sendReceiptEmail

    def setSendReceiptEmail(self, v=True):
        self._sendReceiptEmail = v

    def isSendPaidEmail(self):
        try:
            if self._sendPaidEmail:
                pass
        except AttributeError, e:
            self._sendPaidEmail = False
        return self._sendPaidEmail

    def setSendPaidEmail(self, v=True):
        self._sendPaidEmail = v

    def setTitle(self, newName):
        self.title = newName.strip()

    def getTitle(self):
        return self.title

    def setAnnouncement(self, newDesc):
        self.announcement = newDesc.strip()

    def getAnnouncement(self):
        return self.announcement

    def setUsersLimit(self, newLimit):
        if isinstance(newLimit, int):
            self.usersLimit = newLimit
        elif isinstance(newLimit, str):
            if newLimit.strip() == "":
                self.usersLimit = 0
            else:
                self.usersLimit = int(newLimit.strip())
        if self.usersLimit < 0:
            self.usersLimit = 0

    def getUsersLimit(self):
        return self.usersLimit

    def isFull(self):
        if self.usersLimit != 0:
            return len(self.getConference().getRegistrants()) >= self.usersLimit
        return False

    def setStartRegistrationDate(self, sd):
        self.startRegistrationDate = datetime(sd.year, sd.month, sd.day, 0, 0, 0)

    def getStartRegistrationDate(self):
        return timezone(self.getTimezone()).localize(self.startRegistrationDate)

    def setEndRegistrationDate(self, ed):
        self.endRegistrationDate = datetime(ed.year, ed.month, ed.day, 23, 59, 59)

    def getEndRegistrationDate(self):
        return timezone(self.getTimezone()).localize(self.endRegistrationDate)

    def getAllowedEndRegistrationDate(self):
        if self.getEndExtraTimeUnit() == 'days':
            delta = timedelta(days=self.getEndExtraTimeAmount())
        else:
            delta = timedelta(weeks=self.getEndExtraTimeAmount())
        return timezone(self.getTimezone()).localize(self.endRegistrationDate + delta)

    def setEndExtraTimeAmount(self, value):
        self._endExtraTimeAmount = value

    def getEndExtraTimeAmount(self):
        try:
            return self._endExtraTimeAmount
        except AttributeError:
            self._endExtraTimeAmount = 0
            return self._endExtraTimeAmount

    def setEndExtraTimeUnit(self, value):
        self._endExtraTimeUnit = value

    def getEndExtraTimeUnit(self):
        try:
            return self._endExtraTimeUnit
        except AttributeError:
            self._endExtraTimeUnit = 'days'
            return self._endExtraTimeUnit

    def setModificationEndDate(self, ed):
        if ed:
            self.modificationEndDate = datetime(ed.year, ed.month, ed.day, 23, 59, 59)
        else:
            self.modificationEndDate = None

    def getModificationEndDate(self):
        try:
            if self.modificationEndDate:
                return timezone(self.getTimezone()).localize(self.modificationEndDate)
        except AttributeError, e:
            pass
        return None

    def inModificationPeriod(self):
        if self.getModificationEndDate() is None:
            return False
        date = nowutc()
        sd = self.getStartRegistrationDate()
        ed = self.getModificationEndDate()
        return date <= ed and date >= sd

    def inRegistrationPeriod(self, date=None):
        if date is None:
            date = nowutc()
        sd = self.getStartRegistrationDate()
        ed = self.getAllowedEndRegistrationDate()
        return date <= ed and date >= sd

    def setContactInfo(self, ci):
        self.contactInfo = ci

    def getContactInfo(self):
        return self.contactInfo

    def getStatuses(self):
        try:
            if self._statuses:
                pass
        except AttributeError, e:
            self._statuses = {}
        return self._statuses

    def _generateStatusId(self):
        try:
            if self._statusesGenerator:
                pass
        except AttributeError, e:
            self._statusesGenerator = Counter()
        return self._statusesGenerator

    def getStatusesList(self, sort=True):
        v = self.getStatuses().values()
        if sort:
            v.sort(Status._cmpCaption)
        return v

    def getStatusById(self, id):
        if self.getStatuses().has_key(id):
            return self.getStatuses()[id]
        return None

    def addStatus(self, st):
        st.setId(str(self._generateStatusId().newCount()))
        self.getStatuses()[st.getId()] = st
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

    def _convertPersonalData(self):
        if isinstance(self.personalData, PersonalDataForm):
            return
        pd = PersonalDataForm(self)
        self.addGeneralSectionForm(pd, True, 0)
        for f in pd.getSortedFields():
            f.setDisabled(not self.personalData.getDataItem(f.getPDField()).isEnabled())
            f.setMandatory(self.personalData.getDataItem(f.getPDField()).isMandatory())
        for registrant in self.getConference().getRegistrants().itervalues():
            mg = MiscellaneousInfoGroup(registrant, pd)
            registrant.addMiscellaneousGroup(mg)
            for f in pd.getSortedFields():
                val = getattr(registrant, '_' + f.getPDField())
                # radiobuttons are numerically indexed
                if f.getCaption() == "Title":
                    try:
                        val = str(TitlesRegistry._items.index(val))
                    except ValueError:
                        # can happen for older events with obsolete titles
                        val = "0"

                fakeParams = {f.getInput().getHTMLName(): val}
                f.getInput().setResponseValue(mg.getResponseItemById(f.getId()), fakeParams, registrant, mg, override=True, validate=False)
        self.personalData = pd

    def getPersonalData(self):
        self._convertPersonalData()
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
            self.generalSectionForms = {}
        return self.generalSectionForms

    def getGeneralSectionFormById(self, id):
        return self.getGeneralSectionForms().get(id, None)

    def getGeneralSectionFormsList(self):
        return self.getGeneralSectionForms().values()

    def addGeneralSectionForm(self, gsf, preserveTitle=False, pos=None):
        id = str(self._getGeneralSectionGenerator().newCount())
        while self.getGeneralSectionFormById(id) is not None:
            id = str(self._getGeneralSectionGenerator().newCount())
        gsf.setId(id)
        if not preserveTitle:
            gsf.setTitle("Miscellaneous information %s" % gsf.getId())
        self.generalSectionForms[gsf.getId()] = gsf
        self.addToSortedForms(gsf, pos)
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
        except AttributeError, e:
            self._sortedForms = []
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
            i = len(self.getSortedForms())
        try:
            self.getSortedForms().remove(form)
        except ValueError, e:
            pass
        self.getSortedForms().insert(i, form)
        self.notifyModification()
        return True

    def removeFromSortedForms(self, form):
        try:
            self.getSortedForms().remove(form)
        except ValueError, e:
            return False
        self.notifyModification()
        return True

    def getLocator(self):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the RegistrationForm instance """
        if self.getConference() is None:
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
            se.delete()  # It'll decrease the no of places
        for mg in reg.getMiscellaneousGroupList():
            for item in mg.getResponseItemList():
                item.getGeneralField().getInput()._beforeValueChange(item, False)
        for attachment in reg.getAttachments().keys():
            reg.deleteFile(attachment)

    def delete(self):
        self.getSessionsForm().clearSessionList()
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def notifyModification(self):
        self._p_changed = 1
        self._conf.notifyModification()

    def getETicket(self):
        try:
            return self._eTicket
        except AttributeError:
            self._eTicket = eticket.ETicket()
            return self._eTicket


class Notification(Persistent):

    def __init__(self):
        self._toList = PersistentList()
        self._ccList = PersistentList()

    def clone(self):
        n = Notification()
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
                session1 = i18nformat("""--_("not selected")--""")
                if len(sessionList) > 0:
                    session1 = sessionList[0].getTitle()
                session2 = i18nformat("""--_("not selected")--""")
                if len(sessionList) > 1:
                    session2 = sessionList[1].getTitle()
                text = i18nformat("""%s
- _("First priority"): %s
- _("Other option"): %s
""") % (self._printTitle(sessionForm.getTitle()), session1, session2)
            else:
                sessionListText = []
                for s in sessionList:
                    sessionListText.append("\n%s" % s.getTitle())
                text = """%s%s
""" % (self._printTitle(sessionForm.getTitle()), "".join(sessionListText))
        return text

    def _printAccommodation(self, accommodationForm, accommodation):
        text = ""
        if accommodationForm.isEnabled():
            accoType = i18nformat("""--_("not selected")--""")
            if accommodation.getAccommodationType() is not None:
                accoType = accommodation.getAccommodationType().getCaption()
            text = i18nformat("""%s- _("Arrival date"): %s
- _("Departure date"): %s
- _("Accommodation type"): %s""") % (self._printTitle(accommodationForm.getTitle()), \
                            accommodation.getArrivalDate().strftime("%d %B %Y"), \
                            accommodation.getDepartureDate().strftime("%d %B %Y"), \
                            accoType)
        return text

    def _printSocialEvents(self, socialEventForm, socialEvents):
        text = ""
        if socialEventForm.isEnabled():
            se = []
            for item in socialEvents:
                se.append(_("- %s [%s place(s) needed]") % (item.getCaption(), item.getNoPlaces()))
            text = ""
            if se != []:
                text = """%s
%s
""" % (self._printTitle(socialEventForm.getTitle()), "\n".join(se) or i18nformat("""--_("No social events selected")--"""))
        return text

    def _printReasonParticipation(self, reasonParticipationForm, reasonParticipation):
        text = ""
        if reasonParticipationForm.isEnabled():
            text = """%s%s
                    """ % (self._printTitle(reasonParticipationForm.getTitle()), reasonParticipation)
        return text

    def _printTitle(self, title):
        sep = '-----------------------------------'
        return "\n%s\n%s\n%s\n\n" % (sep, title, sep)

    def _formatValue(self, fieldInput, value):
        try:
            value = str(fieldInput.getValueDisplay(value))
        except:
            value = str(value).strip()
        if len(value) > 50:
            value = '\n\n%s\n' % value
        return value

    def _printMiscellaneousInfo(self, gs, mig):
        text = []
        if gs.isEnabled():
            if mig is not None:
                noitems = True
                text.append(self._printTitle(mig.getTitle()))
                #Mods to support sorting fields
                #for f in gs.getFields():
                for f in gs.getSortedFields():
                    mii = mig.getResponseItemById(f.getId())
                    if mii is not None:
                        noitems = False
                        caption = mii.getCaption()
                        value = mii.getValue()
                        fieldInput = mii.getGeneralField().getInput()

                        isLabel = isinstance(fieldInput, LabelInput)
                        if isLabel and mii.isBillable():
                            value = "%s %s" % (mii.getPrice(), mii.getCurrency())
                        elif isLabel:
                            value = ""

                        if isLabel and not value:
                            text.append("""- %s\n""" % caption)
                        else:
                            text.append("""- %s: %s\n""" % (caption, self._formatValue(fieldInput, value)))
                if noitems:
                    text.append("""-- no values --\n""")
                text.append("\n")
        return "".join(text)

    def _printAllSections(self, regForm, rp):
        sects = []
        for formSection in regForm.getSortedForms():
            if formSection.getId() == "reasonParticipation":
                sects.append("""\n%s""" % self._printReasonParticipation(formSection, rp.getReasonParticipation()))
            elif formSection.getId() == "sessions":
                sects.append("""\n%s""" % self._printSessions(formSection, rp.getSessionList()))
            elif formSection.getId() == "accommodation":
                sects.append("""\n%s""" % self._printAccommodation(formSection, rp.getAccommodation()))
            elif formSection.getId() == "socialEvents":
                sects.append("""\n%s""" % self._printSocialEvents(formSection, rp.getSocialEvents()))
            elif formSection.getId() == "furtherInformation":
                pass
            else:
                sects.append("""%s""" % self._printMiscellaneousInfo(formSection, rp.getMiscellaneousGroupById(formSection.getId())))
        return "".join(s.decode('utf-8') for s in sects).encode('utf-8')

    def _cleanBody(self, body):
        # format the line-breaks in unix-style
        body = re.sub(r'\r\n', '\n', body)

        # clean the extra lines and space
        body = re.sub(r'\n(\s*\n){2,}', '\n\n', body)

        return body

    def createEmailNewRegistrant(self, regForm, rp):
        """
            Creates an email to be sent to the user after registration
        """
        fromAddr = regForm.getNotificationSender()
        url = urlHandlers.UHConferenceDisplay.getURL(regForm.getConference())

#        if rp.getConference().getModPay().isActivated():
        if rp.getConference().getModPay().isActivated() and rp.doPay():
            epaymentLink = "If you haven't paid for your registration yet, you can do it at %s" % urlHandlers.UHConfRegistrationFormCreationDone.getURL(rp)
            paymentWarning = ", but please, do not forget to proceed with the payment if you haven't done it yet (see the link at the end of this email)."
        else:
            epaymentLink = ""
            paymentWarning = "."

        subject = _("""New registrant in '%s': %s""") % (strip_ml_tags(regForm.getConference().getTitle()), rp.getFullName())
        body = i18nformat("""
_("Event"): %s
_("Registrant Id"): %s
%s
""") % (url, rp.getId(), \
                     self._printAllSections(regForm, rp))

        # send mail to organisers
        if self.getToList() != [] or self.getCCList() != []:
            bodyOrg = _("""
There is a new registrant (%s) in '%s'. See information below:

%s
""") % (rp.getFullName(), strip_ml_tags(regForm.getConference().getTitle()), body)
            bodyOrg = self._cleanBody(bodyOrg)
            maildata = {"fromAddr": fromAddr, "toList": self.getToList(), "ccList": self.getCCList(),
                        "subject": subject, "body": bodyOrg}
            GenericMailer.send(GenericNotification(maildata))
        # send mail to participant

        bodyReg = _("""
Congratulations, your registration to %s was successful%s See your information below:

%s
%s
""") % (strip_ml_tags(regForm.getConference().getTitle()), paymentWarning, body, epaymentLink)

        return {
            "fromAddr": fromAddr,
            "toList": [rp.getEmail().strip()],
            "subject": subject,
            "body": self._cleanBody(bodyReg)
        }

    def sendEmailNewRegistrant(self, regForm, rp):
        """
            Creates and sends an email to the user after registration.
            Returns True if suceeded otherwise False.
        """
        email = self.createEmailNewRegistrant(regForm, rp)
        if email:
            GenericMailer.send(GenericNotification(email))
            return True
        else:
            return False

    def sendEmailNewRegistrantDetailsPay(self, regForm, registrant):
        if not registrant.getConference().getModPay().isEnableSendEmailPaymentDetails():
            return
        fromAddr = regForm.getNotificationSender()
        date = registrant.getConference().getStartDate()
        getTitle = strip_ml_tags(registrant.getConference().getTitle())
        idRegistrant = registrant.getIdPay()
        detailPayment = registrant.getConference().getModPay().getPaymentDetails()
        subject = _("""Payment summary for '%s': %s""") % (strip_ml_tags(registrant.getConference().getTitle()), registrant.getFullName())
        body = _("""
Please use this information for your payment (except for e-payment):\n
- date conference    : %s
- name conference    : %s
- registration id    : %s
- detail of payment  : \n%s
""") % (date, getTitle, idRegistrant, strip_ml_tags(detailPayment))
        booking = []
        total = 0
        booking.append(_("""{0}{1}{2}{3}""".format("Quantity".ljust(20), "Item".ljust(50),
                                                   "Unit price".ljust(15), "Cost".ljust(20))))
        #All billable general fields
        for gsf in registrant.getMiscellaneousGroupList():
            miscGroup = registrant.getMiscellaneousGroupById(gsf.getId())
            if miscGroup is not None:
                for miscItem in miscGroup.getResponseItemList():
                    price = 0.0
                    quantity = 0
                    caption = miscItem.getCaption()
                    currency = miscItem.getCurrency()
                    value = ""
                    if miscItem is not None:
                        v = miscItem.getValue()
                        if miscItem.isBillable():
                            value = miscItem.getValue()
                            price = string.atof(miscItem.getPrice())
                            quantity = miscItem.getQuantity()
                            total += price * quantity
                    if value != "":
                        value = ":%s" % value
                    if(quantity > 0):
                        booking.append("{0}{1}{2}{3}".format(str(quantity).ljust(20),
                            "{0} : {1}{2}".format(miscGroup.getTitle(), caption, value).ljust(50), str(price).ljust(15),
                            "{0} {1}".format(price * quantity, currency).ljust(20)))
        #All billable standard fields (accommodation, sessions, social events)
        for bf in registrant.getBilledForms():
            for item in bf.getBilledItems():
                caption = item.getCaption()
                currency = item.getCurrency()
                price = item.getPrice()
                quantity = item.getQuantity()
                total += price * quantity
                if quantity > 0:
                    booking.append("\n{0}{1}{2}{3}".format(str(quantity).ljust(20), caption.ljust(50),
                                                           str(price).ljust(15),
                                                           "{0} {1}".format(price * quantity, currency).ljust(20)))

        booking.append("{0}{1}".format("TOTAL".ljust(85), "{0}{1}".format(total, regForm.getCurrency()).ljust(20)))
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
        paymentMsg = _("If you haven't paid for your registration yet, you can do it at %s") % urlHandlers.UHConfRegistrationFormCreationDone.getURL(registrant)
        if registrant.getEmail().strip() != "":
            bodyReg = _("""%s\n\n%s\n\n%s\n\n%s""") % (
                registrant.getConference().getModPay().getPaymentReceiptMsg(),
                "\n".join(booking), body, paymentMsg)
            to = registrant.getEmail().strip()
            maildata = { "fromAddr": fromAddr, "toList": [to], "subject": subject, "body": bodyReg }
            GenericMailer.send(GenericNotification(maildata))

    def sendEmailNewRegistrantConfirmPay(self, regForm, registrant):
        fromAddr = regForm.getNotificationSender()
        date = registrant.getConference().getStartDate()
        getTitle = strip_ml_tags(registrant.getConference().getTitle())
        idRegistrant = registrant.getIdPay()

        subject = _("""Payment successful for '%s': %s""") % (strip_ml_tags(registrant.getConference().getTitle()), registrant.getFullName())
        body = _("""- detail of payment  : \n%s
- date conference    : %s
- name conference    : %s
- registration id    : %s""") % (registrant.getTransactionInfo().getTransactionTxt(), date, getTitle, idRegistrant)
        booking = []
        total = 0
        booking.append("""Quantity\t\tItem\t\tunit.price\t\tCost""")
        for gsf in registrant.getMiscellaneousGroupList():
            miscGroup = registrant.getMiscellaneousGroupById(gsf.getId())
            if miscGroup is not None:
                for miscItem in miscGroup.getResponseItemList():
                    price = 0.0
                    quantity = 0
                    caption = miscItem.getCaption()
                    currency = miscItem.getCurrency()
                    v = ""
                    if miscItem is not None:
                        v = miscItem.getValue()
                        if miscItem.isBillable():
                            v = miscItem.getValue()
                            price = string.atof(miscItem.getPrice())
                            quantity = miscItem.getQuantity()
                            total += price * quantity
                    if v != "":
                        v = ":%s" % v
                    if(quantity > 0):
                         booking.append("""%i\t\t%s : %s%s\t\t%s\t\t%s %s""" % \
                                        (quantity, gsf.getTitle(), caption, v, price, price * quantity, currency))
        for bf in registrant.getBilledForms():
            for item in bf.getBilledItems():
                caption = item.getCaption()
                currency = item.getCurrency()
                price = item.getPrice()
                quantity = item.getQuantity()
                total += price * quantity
                if quantity > 0:
                    booking.append("""%i\t\t%s\t\t%s\t\t%s %s""" % (quantity, caption, price, price * quantity, currency))

        booking.append("""\nTOTAL\t\t\t\t\t\t\t%s %s""" % (total, regForm.getCurrency()))
        # send email to organisers
        if self.getToList() != [] or self.getCCList() != []:
            bodyOrg = _("""
             There is a new registrant (%s) in '%s'. See information below:

                      %s
                      """) % (registrant.getFullName(), strip_ml_tags(registrant.getConference().getTitle()), body)
            maildata = { "fromAddr": fromAddr, "toList": self.getToList(), "ccList": self.getCCList(), "subject": subject, "body": bodyOrg }
            GenericMailer.send(GenericNotification(maildata))
        # send email to participant
        if regForm.isSendPaidEmail() and registrant.getEmail().strip() != "":
            bodyReg = _("""%s\n\n%s\n\n%s""") % (registrant.getConference().getModPay().getPaymentSuccessMsg(),
                                                                "\n".join(booking),
                                                                body)
            to = registrant.getEmail().strip()
            maildata = { "fromAddr": fromAddr, "toList": [to], "subject": subject, "body": bodyReg }
            GenericMailer.send(GenericNotification(maildata))

    def sendEmailModificationRegistrant(self, regForm, rp):
        fromAddr = regForm.getNotificationSender()
        subject = _("""Registration modified for '%s': %s""") % (strip_ml_tags(regForm.getConference().getTitle()), rp.getFullName())
        body = i18nformat("""
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
""") % (rp.getId(), \
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
                     self._printAllSections(regForm, rp))
        if self.getToList() != [] or self.getCCList() != []:
            bodyOrg = _("""
A registrant (%s) has modified his/her registration for '%s'. See information below:

%s
""") % (rp.getFullName(), strip_ml_tags(regForm.getConference().getTitle()), body)
            bodyOrg = self._cleanBody(bodyOrg)
            maildata = { "fromAddr": fromAddr, "toList": self.getToList(), "ccList": self.getCCList(), "subject": subject, "body": bodyOrg }
            GenericMailer.send(GenericNotification(maildata))

    def exportXml(self, xmlGen):
        """Write xml tags about this object in the given xml generator of type XMLGen."""
        xmlGen.openTag("notification")
        xmlGen.writeTag("toList", ", ".join(self.getToList()))
        xmlGen.writeTag("ccList", ", ".join(self.getCCList()))
        xmlGen.closeTag("notification")


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
    _id = ""
    _useLabelCol = True
    _wholeRow = False

    def __init__(self, field):
        self._parent = field

    def getValues(self):
        return {}

    def setValues(self, data):
        pass

    def getParent(self):
        return self._parent

    def setId(cls, id):
        cls._id = id
    setId = classmethod(setId)

    def getId(cls):
        return cls._id
    getId = classmethod(getId)

    def getName(cls):
        return cls._id
    getName = classmethod(getName)

    def getHTMLName(self):
        """
        This method returns the indentifier of the field item in the web form.
        """
        return "*genfield*%s-%s" % (self.getParent().getParent().getId(), self.getParent().getId())

    def getModifLabelCol(self):
        if not self._useLabelCol:
            return ""
        return self._parent.getCaption()

    def useWholeRow(self):
        return self._wholeRow

    def getMandatoryCol(self, item):
        mandatory = ""
        if (item is not None and item.isMandatory()) or self.getParent().isMandatory():
            mandatory = """<span class="regFormMandatoryField">*</span>"""
        return mandatory

    def getModifHTML(self, item, registrant, default=""):
        """
        Method that display the form web which represents this object.
        """
        return "<table><tr>%s</tr></table>" % (self._getModifHTML(item, registrant, default))

    def _getModifHTML(self, item, registrant, default=""):
        """
        Method that should be overwritten by the classes inheriting from this one in order to display
        the form web which represents this object.
        """
        return ""

    def setResponseValue(self, item, params, registrant, mg=None, override=False, validate=True):
        """
        This method shouldn't be called from the classes inheriting from this one (FieldInputType).
        This method fills the attribute "item" (MiscellaneousInfoSimpleItem) with the value the user wrote
        in the registration form.
        """
        if item is None:
            item = MiscellaneousInfoSimpleItem(mg, self.getParent())
            mg.addResponseItem(item)
            self._beforeValueChange(item, True)
        else:
            self._beforeValueChange(item, False)

        self._setResponseValue(item, params, registrant, override=override, validate=validate)
        self._afterValueChange(item)

    def _beforeValueChange(self, item, newItem):
        # if the item had a quantity, make the place available again
        if not newItem and item.getQuantity():
            self.getParent().decreaseNoPlaces()

    def _afterValueChange(self, item):
        # if the item has a quantity now, make the place unavailable
        if item.getQuantity():
            self.getParent().increaseNoPlaces()

    def _setResponseValue(self, item, registrant, params, override=False, validate=True):
        """
        Method that should be overwritten by the classes inheriting from this one in order to get the value written in the form.
        """
        pass

    def _getSpecialOptionsHTML(self):
        price = self._parent.getPrice()
        billable = self._parent.isBillable()
        checked = ""
        if billable:
            checked = "checked=\"checked\""

        html = i18nformat(""" <tr>
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
                           """) % (checked, price)
        return "".join(html)

    def _getDescriptionHTML(self, description):
        return """<span class="inputDescription">%s</span>""" % description

    def clone(self, gf):
        fi = FieldInputs().getAvailableInputKlassById(self.getId())(gf)
        return fi


class TextInput(FieldInputType, Fossilizable):

    fossilizes(IRegFormTextInputFieldFossil)

    _id = "text"

    def getName(cls):
        return "Text"
    getName = classmethod(getName)

    def __init__(self, field):
        FieldInputType.__init__(self, field)
        self._length = ''

    def _getModifHTML(self, item, registrant, default=""):
        description = self._parent.getDescription()
        price = self._parent.getPrice()
        billable = self._parent.isBillable()
        currency = self._parent.getParent().getRegistrationForm().getCurrency()
        htmlName = self.getHTMLName()
        v = default
        if item is not None:
            v = item.getValue()
            price = item.getPrice()
            billable = item.isBillable()
            currency = item.getCurrency()
            htmlName = item.getHTMLName()
        disable = ""
        if (registrant is not None and billable and registrant.getPayed()):
            disable = "disabled=\"true\""
            #pass
        if self._parent.getPDField() == 'email':
            param = """<script>addParam($E('%s'), 'email', %s);</script>""" % (htmlName, 'false' if self._parent.isMandatory() else 'true')
        elif self._parent.isMandatory():
            param = """<script>addParam($E('%s'), 'text', false);</script>""" % htmlName
        else:
            param = ''
        if self.getLength():
            length = 'size="%s"' % self.getLength()
        else:
            length = 'size="60"'
        tmp = """<input type="text" id="%s" name="%s" value="%s" %s %s >%s""" % (htmlName, htmlName, v , disable, length, param)
        tmp = """ <td>%s</td><td align="right" align="bottom">""" % tmp
        if billable:
            tmp = """%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s</td> """ % (tmp, price, currency)
        else:
            tmp = """%s </td> """ % tmp
        if description:
            tmp = """%s</tr><tr><td colspan="2">%s</td>""" % (tmp, self._getDescriptionHTML(description))
        return tmp

    def _setResponseValue(self, item, params, registrant, override=False, validate=True):
        if (registrant is not None and self._parent.isBillable() and registrant.getPayed()):
            #if ( item is not None and item.isBillable()):
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
        v = params.get(self.getHTMLName(), "")
        if not override and self.getParent().isMandatory() and v.strip() == "":
            raise FormValuesError(_("The field \"%s\" is mandatory. Please fill it.") % self.getParent().getCaption())

        item.setQuantity(0)
        item.setValue(v)
        #item.setBillable(self._parent.isBillable())
        #item.setPrice(self._parent.getPrice())
        #item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())

    def _getSpecialOptionsHTML(self):
        return i18nformat("""
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">_("Size in chars")</span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
              <input type="text" name="length" value="%s" />
          </td>
        </tr>""" % self.getLength())

    def clone(self, gf):
        ti = FieldInputType.clone(self, gf)
        ti.setLength(self.getLength())
        return ti

    def getValues(self):
        d = {}
        d["length"] = self.getLength()
        return d

    def setValues(self, data):
        if data.has_key("length"):
            self.setLength(data.get("length"))

    def getLength(self):
        try:
            if self._length: pass
        except AttributeError:
            self._length = ''
        return self._length

    def setLength(self, value):
        self._length = value


class TelephoneInput(FieldInputType, Fossilizable):

    fossilizes(IRegFormTelephoneInputFieldFossil)

    _id = "telephone"
    _REGEX = r'^(\(\+\d*\)|\+)?\s*(\d(\s*|\-))+$'
    _PATTERN = re.compile(_REGEX)

    def getName(cls):
        return "Telephone"
    getName = classmethod(getName)

    def __init__(self, field):
        FieldInputType.__init__(self, field)
        self._length = ''

    def _getModifHTML(self, item, registrant, default=""):
        description = self._parent.getDescription()
        htmlName = self.getHTMLName()

        v = default
        if item is not None:
            v = item.getValue()
            htmlName = item.getHTMLName()

        disable = ""
        if self._parent.isMandatory():
            param = """<script>
            addParam($E('%s'), 'text', false, function(value) {
              if (!/%s/.test(value)) {
                return "Invalid phone number format";
              }
            });
            </script>""" % (htmlName, TelephoneInput._REGEX)
        else:
            param = ''
        if self.getLength():
            length = 'size="%s"' % self.getLength()
        else:
            length = 'size="30"'
        format = """&nbsp;<span class="inputDescription">(+) 999 99 99 99</span>"""
        tmp = """<input type="text" id="%s" name="%s" value="%s" %s %s>%s%s""" % (htmlName, htmlName, v , disable, length, format, param)
        tmp = """ <td>%s</td>""" % tmp
        if description:
            tmp = """%s</tr><tr><td>%s</td>""" % (tmp, self._getDescriptionHTML(description))
        return tmp

    def _setResponseValue(self, item, params, registrant, override=False, validate=True):
        v = params.get(self.getHTMLName(), "")

        if not override and self.getParent().isMandatory() and v.strip() == "":
            raise FormValuesError(_("The field \"%s\" is mandatory. Please fill it.") % self.getParent().getCaption())

        if validate and v.strip() != '' and not TelephoneInput._PATTERN.match(v):
            raise FormValuesError(_("The field \"%s\" is in wrong format. Please fill it in the correct format: (+) 999 99 99 99") % self.getParent().getCaption())

        v = re.sub(r'\s+|\-+', '', v)

        item.setQuantity(0)
        item.setValue(v)
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())

    def _getSpecialOptionsHTML(self):
        return i18nformat("""
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">_("Size in chars")</span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
              <input type="text" name="length" value="%s" />
          </td>
        </tr>""" % self.getLength())

    def clone(self, gf):
        ti = FieldInputType.clone(self, gf)
        ti.setLength(self.getLength())
        return ti

    def getValues(self):
        d = {}
        d["length"] = self.getLength()
        return d

    def setValues(self, data):
        if data.has_key("length"):
            self.setLength(data.get("length"))

    def getLength(self):
        try:
            if self._length:
                pass
        except AttributeError:
            self._length = ''
        return self._length

    def setLength(self, value):
        self._length = value


class TextareaInput(FieldInputType, Fossilizable):

    fossilizes(IRegFormTextareaInputFieldFossil)

    _id = "textarea"

    def getName(cls):
        return "Textarea"
    getName = classmethod(getName)

    def __init__(self, field):
        FieldInputType.__init__(self, field)
        self._numberOfRows = ''
        self._numberOfColumns = ''

    def _getModifHTML(self, item, registrant, default=""):
        description = self._parent.getDescription()
        price = self._parent.getPrice()
        billable = self._parent.isBillable()
        currency = self._parent.getParent().getRegistrationForm().getCurrency()
        htmlName = self.getHTMLName()
        v = default
        if item is not None:
            v = item.getValue()
            price = item.getPrice()
            billable = item.isBillable()
            currency = item.getCurrency()
            htmlName = item.getHTMLName()
        disable = ""
        if (registrant is not None and billable and registrant.getPayed()):
            disable = "disabled=\"true\""
            #pass

        if description:
            desc = """%s<br/>""" % self._getDescriptionHTML(description)
        else:
            desc = ''

        if self._parent.isMandatory():
            param = """<script>addParam($E('%s'), 'text', false);</script>""" % htmlName
        else:
            param = ''
        cols = self.getNumberOfColumns()
        if not cols:
            cols = 60
        rows = self.getNumberOfRows()
        if not rows:
            rows = 4

        tmp = """%s<textarea id="%s" name="%s" cols="%s" rows="%s" %s >%s</textarea>%s""" % (desc, htmlName, htmlName, cols, rows, disable, v, param)
        tmp = """ <td>%s</td><td align="right" align="bottom">""" % tmp
        tmp = """%s </td> """ % tmp

        return tmp

    def _setResponseValue(self, item, params, registrant, override=False, validate=True):
        if (registrant is not None and self._parent.isBillable() and registrant.getPayed()):
            #if ( item is not None and item.isBillable()):
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
        v = params.get(self.getHTMLName(), "")
        if not override and self.getParent().isMandatory() and v.strip() == "":
            raise FormValuesError(_("The field \"%s\" is mandatory. Please fill it.") % self.getParent().getCaption())
        item.setQuantity(0)
        item.setValue(v)
        #item.setBillable(self._parent.isBillable())
        #item.setPrice(self._parent.getPrice())
        #item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())

    def _getSpecialOptionsHTML(self):
        html = [i18nformat("""
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">_("Number of rows")</span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
              <input type="text" name="numberOfRows" value="%s" />
          </td>
        </tr>""") % self.getNumberOfRows()]

        html.append(i18nformat("""
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">_("Row length")</span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
              <input type="text" name="numberOfColumns" value="%s" />
          </td>
        </tr>""") % self.getNumberOfColumns())
        return "".join(html)

    def clone(self, gf):
        ti = FieldInputType.clone(self, gf)
        ti.setNumberOfRows(self.getNumberOfRows())
        ti.setNumberOfColumns(self.getNumberOfColumns())
        return ti

    def getValues(self):
        d = {}
        d["numberOfRows"] = self.getNumberOfRows()
        d["numberOfColumns"] = self.getNumberOfColumns()
        return d

    def setValues(self, data):
        if data.has_key("numberOfRows"):
            self.setNumberOfRows(data.get("numberOfRows"))
        if data.has_key("numberOfColumns"):
            self.setNumberOfColumns(data.get("numberOfColumns"))

    def getNumberOfRows(self):
        try:
            if self._numberOfRows: pass
        except AttributeError:
            self._numberOfRows = ''
        return self._numberOfRows

    def setNumberOfRows(self, value):
        self._numberOfRows = value

    def getNumberOfColumns(self):
        try:
            if self._numberOfColumns: pass
        except AttributeError:
            self._numberOfColumns = ''
        return self._numberOfColumns

    def setNumberOfColumns(self, value):
        self._numberOfColumns = value


class NumberInput(FieldInputType, Fossilizable):

    fossilizes(IRegFormNumberInputFieldFossil)

    _id = "number"
    _useLabelCol = False

    def getName(cls):
        return "Number"
    getName = classmethod(getName)

    def __init__(self, field):
        FieldInputType.__init__(self, field)
        self._length = ''
        self._minValue = 0

    def _getModifHTML(self, item, registrant, default=""):
        description = self._parent.getDescription()
        price = self._parent.getPrice()
        billable = self._parent.isBillable()
        currency = self._parent.getParent().getRegistrationForm().getCurrency()
        htmlName = self.getHTMLName()
        v = default or self.getMinValue()
        if item is not None:
            v = item.getValue()
            price = item.getPrice()
            billable = item.isBillable()
            currency = item.getCurrency()
            htmlName = item.getHTMLName()

        mandat = "false" if self._parent.isMandatory() else "true"
        if self.getMinValue() != 0:
            extra_check = "IndicoUtil.validate_number({minimum:%s})" % self.getMinValue()
        else:
            extra_check = "function(){}"
        param = """<script>addParam($E('%s'), 'non_negative_int', %s, %s);</script>""" % (htmlName, mandat, extra_check)

        disable = ""
        if (registrant is not None and billable and registrant.getPayed()):
            disable = "disabled=\"true\""
            #pass
        if self.getLength():
            length = 'size="%s"' % self.getLength()
        else:
            length = 'size="6"'
        onkeyup = ""
        if billable:
            onkeyup = """onkeyup="
            var value = ((isNaN(parseInt(this.value, 10)) || parseInt(this.value, 10) < 0) ? 0 : parseInt(this.value, 10)) * %s;
            $E('subtotal-%s').dom.innerHTML = parseInt(value) === parseFloat(value) ? value : value.toFixed(2);"
            """ % (price, htmlName)
        tmp = """<input type="text" id="%s" name="%s" value="%s" %s %s %s /> %s""" % (htmlName, htmlName, v, onkeyup, disable, length, param)
        tmp = """ <td>%s</td>""" % tmp
        if billable:
            subTotal = (float(price) * int(v) or 0)
            tmp = """%s<td align="right" align="bottom">&nbsp;&nbsp;<span>%s&nbsp;%s</span><span class="regFormSubtotal">Total: <span id="subtotal-%s">%s</span>&nbsp;%s</span></td> """ % (tmp, price, currency, htmlName, subTotal, currency)
        if description:
            tmp = """%s</tr><tr><td colspan="2">%s</td>""" % (tmp, self._getDescriptionHTML(description))
        return tmp

    def _setResponseValue(self, item, params, registrant, override=False, validate=True):
        v = params.get(self.getHTMLName(), "")
        quantity = 0
        if (registrant is not None and self._parent.isBillable() and registrant.getPayed()):
            #if ( item is not None and item.isBillable() ):
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
        if not override and self.getParent().isMandatory() and v.strip() == "":
            raise FormValuesError(_("The field \"%s\" is mandatory. Please fill it.") % self.getParent().getCaption())
        if not override and self.getParent().isMandatory() and (not v.isalnum() or int(v) < 0):
            raise FormValuesError(_("The field \"%s\" is mandatory. Please fill it with a number.") % self.getParent().getCaption())
        if not v.isalnum() or int(v) < 1:
            quantity = 0
        else:
            quantity = int(v)
        if v.strip() != '' and quantity < self.getMinValue():
            raise FormValuesError(_("The field \"%s\" needs to be filled with a number greater than or equal to %d.") % (self.getParent().getCaption(), self.getMinValue()))
        item.setQuantity(quantity)
        item.setValue(quantity)
        item.setBillable(self._parent.isBillable())
        item.setPrice(self._parent.getPrice())
        item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())

    def _getSpecialOptionsHTML(self):
        price = self._parent.getPrice()
        billable = self._parent.isBillable()
        checked = ""
        if billable:
            checked = "checked=\"checked\""

        return i18nformat("""
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">_("Min. value")</span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
              <input type="text" name="minValue" value="%s" />
          </td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">_("Size in chars")</span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
              <input type="text" name="length" value="%s" />
          </td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">Is Billable</span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
            <input type="checkbox" name="billable" size="60" %s> _("(uncheck if it is not billable)")
          </td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat"> _("Price (multiplied with entered number)")</span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
            <input type="text" name="price" size="60" value=%s>
          </td>
        </tr>""" % (self.getMinValue(), self.getLength(), checked, price))

    def clone(self, gf):
        ni = FieldInputType.clone(self, gf)
        ni.setLength(self.getLength())
        ni.setMinValue(self.getMinValue())
        return ni

    def getValues(self):
        d = {}
        d["length"] = self.getLength()
        d["minValue"] = self.getMinValue()
        return d

    def setValues(self, data):
        if data.has_key("length"):
            self.setLength(data.get("length"))
        if data.has_key("minValue"):
            self.setMinValue(int(data.get("minValue") or 0))

    def getLength(self):
        try:
            if self._length: pass
        except AttributeError:
            self._length = ''
        return self._length

    def setLength(self, value):
        self._length = value

    def getMinValue(self):
        try:
            if self._minValue: pass
        except AttributeError:
            self._minValue = 0
        return self._minValue

    def setMinValue(self, value):
        self._minValue = value

    def getModifLabelCol(self):
        return self._parent.getCaption()


class LabelInput(FieldInputType, Fossilizable):

    fossilizes(IRegFormLabelInputFieldFossil)

    _id = "label"
    _wholeRow = True

    def getName(cls):
        return "Label"
    getName = classmethod(getName)

    def _getModifHTML(self, item, registrant, default=""):
        description = self._parent.getDescription()
        price = self._parent.getPrice()
        billable = self._parent.isBillable()
        currency = self._parent.getParent().getRegistrationForm().getCurrency()
        v = default
        if item is not None:
            v = item.getValue()
            price = item.getPrice()
            billable = item.isBillable()
            currency = item.getCurrency()
            #pass
        tmp = """ <td align="right" valign="bottom">"""
        if billable:
            tmp = """%s&nbsp;&nbsp;%s&nbsp;%s</td> """ % (tmp, price, currency)
        else:
            tmp = """%s </td> """ % tmp
        if description:
            tmp = """%s</tr><tr><td colspan="2">%s</td>""" % (tmp, self._getDescriptionHTML(description))
        return tmp

    def _setResponseValue(self, item, params, registrant, override=False, validate=True):
        if (registrant is not None and self._parent.isBillable() and registrant.getPayed()):
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


class CheckboxInput(FieldInputType, Fossilizable):

    fossilizes(IRegFormCheckboxInputFieldFossil)

    _id = "checkbox"
    _useLabelCol = False

    def getName(cls):
        return "Multiple choices/checkbox"
    getName = classmethod(getName)

    def _getModifHTML(self, item, registrant, default=""):
        disable = ""
        checked = ""
        mandatory = ""
        caption = self._parent.getCaption()
        description = self._parent.getDescription()
        price = self._parent.getPrice()
        billable = self._parent.isBillable()
        currency = self._parent.getParent().getRegistrationForm().getCurrency()
        htmlName = self.getHTMLName()
        v = default
        quantity = 0
        if item is not None:
            v = item.getValue()
            price = item.getPrice()
            billable = item.isBillable()
            currency = item.getCurrency()
            htmlName = item.getHTMLName()
            quantity = item.getQuantity()
            mandatory = """<span class="regFormMandatoryField">*</span>""" if self._parent.isMandatory() else ""
        if (registrant is not None and billable and registrant.getPayed()) or (not self.getParent().hasAvailablePlaces() and not quantity):
            disable = "disabled=\"disabled\""
        if v == "yes":
            checked = "checked=\"checked\""
        pm = ''
        if self._parent.isMandatory():
            pm = """<script>addParam($E('%s'), 'checkBox', false);</script>""" % htmlName
        tmp = """<input type="checkbox" id="%s" name="%s" %s %s> %s %s%s""" % (htmlName, htmlName, checked, disable, caption, mandatory, pm)
        tmp = """ <td>%s</td><td align="right" align="bottom">""" % tmp
        if billable:
            tmp = """%s&nbsp;&nbsp;%s&nbsp;%s """ % (tmp, price, currency)
        if self.getParent().getPlacesLimit():
            tmp += """&nbsp;<span class='placesLeft'>[%s place(s) left]</span>""" % (self.getParent().getNoPlacesLeft())
        tmp += """</td>"""
        if description:
            tmp = """%s</tr><tr><td colspan="2">%s</td>""" % (tmp, self._getDescriptionHTML(description))
        return tmp

    def _setResponseValue(self, item, params, registrant, override=False, validate=True):
        if (registrant is not None and self._parent.isBillable() and registrant.getPayed()):
            #if ( item is not None and item.isBillable()):
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
        if params.has_key(self.getHTMLName()):
            item.setValue("yes")
            item.setQuantity(1)
        elif not override and self.getParent().isMandatory():
            raise FormValuesError(_('The checkbox "%s" is mandatory. Please enable it.') % self.getParent().getCaption())
        else:
            item.setValue("no")
            item.setQuantity(0)
        item.setBillable(self._parent.isBillable())
        item.setPrice(self._parent.getPrice())
        item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())

    def _getSpecialOptionsHTML(self):
        html = FieldInputType._getSpecialOptionsHTML(self)
        html += i18nformat("""<tr>
                  <td class="titleCellTD"><span class="titleCellFormat"> _("Places (0 for unlimited)")</span></td>
                  <td bgcolor="white" class="blacktext" width="100%%">
                    <input type="text" name="placesLimit" size="60" value=%s>
                  </td>
                </tr>""") % (self._parent.getPlacesLimit())
        return html


class YesNoInput(FieldInputType, Fossilizable):

    fossilizes(IRegFormYesNoInputFieldFossil)

    _id = "yes/no"

    def getName(cls):
        return "Yes/No"
    getName = classmethod(getName)

    def _getModifHTML(self, item, registrant, default=""):
        description = self._parent.getDescription()
        price = self._parent.getPrice()
        billable = self._parent.isBillable()
        currency = self._parent.getParent().getRegistrationForm().getCurrency()
        htmlName = self.getHTMLName()
        v = default
        if item is not None:
            v = item.getValue()
            price = item.getPrice()
            billable = item.isBillable()
            currency = item.getCurrency()
            htmlName = item.getHTMLName()
        disable = ""

        if self._parent.isMandatory():
            param = """<script>addParam($E('%s'), 'text', false);</script>""" % htmlName
        else:
            param = ''

        checkedYes = ""
        checkedNo = ""
        if (registrant is not None and billable and registrant.getPayed()):
            disable = "disabled=\"true\""
            #pass
        if v == "yes":
            checkedYes = "selected"
        elif v == "no":
            checkedNo = "selected"

        placesInfo = ""
        if self.getParent().getPlacesLimit():
            placesInfo = """&nbsp;[%s place(s) left]""" % (self.getParent().getNoPlacesLeft())
            if v != "yes" and not self.getParent().hasAvailablePlaces():
                checkedYes += " disabled"
        tmp = """<select id="%s" name="%s" %s><option value="">-- Choose a value --</option><option value="yes" %s>yes%s</option><option value="no" %s>no</option></select>%s""" % (htmlName, htmlName, disable, checkedYes, placesInfo, checkedNo, param)
        tmp = """ <td>%s</td><td align="right" align="bottom">""" % tmp
        if billable:
            tmp = """%s&nbsp;&nbsp;%s&nbsp;%s</td> """ % (tmp, price, currency)
        else:
            tmp = """%s </td> """ % tmp
        if description:
            tmp = """%s</tr><tr><td colspan="2">%s</td>""" % (tmp, self._getDescriptionHTML(description))
        return tmp

    def _setResponseValue(self, item, params, registrant, override=False, validate=True):
        if (registrant is not None and self._parent.isBillable() and registrant.getPayed()):
            #if ( item is not None and item.isBillable()):
            #    return
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
        v = params.get(self.getHTMLName())

        if not override and self.getParent().isMandatory() and v.strip() == "":
            raise FormValuesError(_("The field \"%s\" is mandatory. Please fill it.") % self.getParent().getCaption())

        if v == "yes":
            item.setQuantity(1)
        else:
            item.setQuantity(0)
        item.setValue(v)
        item.setBillable(self._parent.isBillable())
        item.setPrice(self._parent.getPrice())
        item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())

    def _getSpecialOptionsHTML(self):
        html = FieldInputType._getSpecialOptionsHTML(self)
        html += i18nformat("""<tr>
                  <td class="titleCellTD"><span class="titleCellFormat"> _("Places (0 for unlimited)")</span></td>
                  <td bgcolor="white" class="blacktext" width="100%%">
                    <input type="text" name="placesLimit" size="60" value=%s>
                  </td>
                </tr>""") % (self._parent.getPlacesLimit())
        return html


class FileInput(FieldInputType, Fossilizable):

    fossilizes(IRegFormFileInputFieldFossil)

    _id = "file"

    def getName(cls):
        return "File"
    getName = classmethod(getName)

    def getValueDisplay(self, value):
        uh = (urlHandlers.UHRegistrantAttachmentFileAccess if request.blueprint == 'event_mgmt' else
              urlHandlers.UHFileAccess)
        return """<a href="%s">%s</a>""" % (uh.getURL(value), value.getFileName())

    def _getModifHTML(self, item, registrant, default=None):
        from MaKaC.webinterface.pages.registrationForm import WFileInputField

        wc = WFileInputField(self, item, default)
        return wc.getHTML()

    def _setResponseValue(self, item, params, registrant, override=False, validate=True):
        v = params.get(self.getHTMLName(), "")
        newValueEmpty = v.strip() == "" if isinstance(v, str) else v.filename == ""
        if not override and self.getParent().isMandatory() and newValueEmpty:
            raise FormValuesError(_("The field \"%s\" is mandatory. Please fill it.") % self.getParent().getCaption())

        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())
        # There was no file saved on DB
        if item.getValue() is None:
            if not newValueEmpty:  # user submits a new file
                f = registrant.saveFile(v)
                item.setValue(f)
        # There was already a file on DB
        # if 'str': it means that we are receiving the name of the already existing file. Do not modify.
        # if file descriptor: replace previous file with new one
        # if 'empty' value: just remove
        elif not isinstance(v, str):
            # delete
            registrant.deleteFile(item.getValue().getId())
            item.setValue(None)
            # new file
            if not newValueEmpty:
                f = registrant.saveFile(v)
                item.setValue(f)

    def _getSpecialOptionsHTML(self):
        return ""

    def clone(self, gf):
        ti = FieldInputType.clone(self, gf)
        return ti


class RadioItem(Persistent, Fossilizable):

    fossilizes(IRegFormRadioItemFossil)

    def __init__(self, parent):
        self._parent = parent
        self._id = ""
        self._caption = ""
        self._billable = False
        self._price = ""
        self._enabled = True
        self._placesLimit = 0
        self._currentNoPlaces = 0

    def setValues(self, data):
        if data.has_key("caption"):
            self.setCaption(data["caption"])
        if data.has_key("isBillable"):
            self.setBillable(data["isBillable"])
        if data.has_key("price"):
            self.setPrice(data["price"])
        if data.has_key("isEnabled"):
            self.setEnabled(data["isEnabled"])
        if data.has_key("placesLimit"):
            self.setPlacesLimit(data["placesLimit"])

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getCaption(self):
        return self._caption

    def setCaption(self, cap):
        if self._caption != cap:
            self.updateRegistrantSelection(cap)
        self._caption = cap

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

    def setBillable(self, v):
        self._billable = v

    def getPrice(self):
        try:
            return self._price
        except:
            self.setPrice(False)
        return self._price

    def setPrice(self, price):
        if price:
            match = PRICE_PATTERN.match(price)
            if match:
                price = match.group(1)
            else:
                raise MaKaCError(_('The price is in incorrect format!'))
        self._price = price

    def getPlacesLimit(self):
        try:
            if self._placesLimit:
                pass
        except AttributeError, e:
            self._placesLimit = 0
        return self._placesLimit

    def setPlacesLimit(self, limit):
        if limit == "":
            limit = "0"
        try:
            l = int(limit)
        except ValueError:
            raise FormValuesError(_("Please enter a number for the limit of places"))
        self._placesLimit = l
        self.updateCurrentNoPlaces()

    def getCurrentNoPlaces(self):
        try:
            if self._currentNoPlaces:
                pass
        except AttributeError:
            self._currentNoPlaces = 0
        return self._currentNoPlaces

    def hasAvailablePlaces(self):
        if not self.getPlacesLimit():
            return True
        return (self.getCurrentNoPlaces() < self.getPlacesLimit())

    def getNoPlacesLeft(self):
        return self.getPlacesLimit() - self.getCurrentNoPlaces()

    def increaseNoPlaces(self):
        if self.getPlacesLimit() > 0 :
            if self.getCurrentNoPlaces() >= self.getPlacesLimit():
                raise FormValuesError(_("""The place limit has been exceeded."""))
            self._currentNoPlaces += 1

    def decreaseNoPlaces(self):
        if self.getPlacesLimit() > 0 and self.getCurrentNoPlaces() > 0:
            self._currentNoPlaces -= 1

    def updateCurrentNoPlaces(self):
        # self -> RadioGroupInput -> GeneralField -> GeneralSectionForm
        gf = self._parent._parent
        self._currentNoPlaces = 0
        gsf = gf._parent
        regform = gsf.getRegistrationForm()
        for reg in regform.getConference().getRegistrantsList():
            mg = reg.getMiscellaneousGroupById(gsf.getId())
            if not mg:
                continue
            gf.getId() # for some reason it's empty when calling it for the first time
            item = mg.getResponseItemById(gf.getId())
            if item is not None and item.getQuantity() and item.getValue() == self.getCaption():
                self.increaseNoPlaces()

    def updateRegistrantSelection(self, caption):
        gf = self._parent._parent
        self._currentNoPlaces = 0
        gsf = gf._parent
        regform = gsf.getRegistrationForm()
        for reg in regform.getConference().getRegistrantsList():
            mg = reg.getMiscellaneousGroupById(gsf.getId())
            if not mg:
                continue
            item = mg.getResponseItemById(gf.getId())
            if item is not None and item.getQuantity() and item.getValue() == self.getCaption():
                item.setValue(caption)
                self.increaseNoPlaces()

    def clone(self, parent):
        ri = RadioItem(parent)
        ri.setCaption(self.getCaption())
        ri.setBillable(self.isBillable())
        ri.setPrice(self.getPrice())
        ri.setEnabled(self.isEnabled())
        ri.setPlacesLimit(self.getPlacesLimit())
        return ri

    def _cmpCaption(r1, r2):
        return cmp(r1.getCaption(), r2.getCaption())
    _cmpCaption = staticmethod(_cmpCaption)


class RadioGroupInput(FieldInputType, Fossilizable):

    fossilizes(IRegFormRadioGroupInputFieldFossil)

    _id = "radio"

    def getName(cls):
        return "Multiple options/One choice"
    getName = classmethod(getName)

    def __init__(self, field):
        FieldInputType.__init__(self, field)
        self._items = []
        self._radioItemGenerator = Counter()
        self._defaultItem = None
        self._inputType = "radiogroup"
        self._emptyCaption = '-- Choose a value --'

    def getValues(self):
        d = {}
        d["radioitems"] = []
        for i in self.getItemsList():
            tmp = {}
            tmp["caption"] = i.getCaption()
            tmp["billable"] = i.isBillable()
            tmp["price"] = i.getPrice()
            tmp["isEnabled"] = i.isEnabled()
            tmp["placesLimit"] = i.getPlacesLimit()
            tmp["id"] = i.getId()
            d["radioitems"].append(tmp)
        d["defaultItem"] = self.getDefaultItem()
        d["inputType"] = self.getInputType()
        d["emptyCaption"] = self.getEmptyCaption()
        return d

    def setValues(self, data):
        if "radioitems" in data:
            for i, itemValues in enumerate(data.get("radioitems", [])):
                item = self.getItemById(itemValues.get('id'))
                if item is None:
                    self.createItem(itemValues, i)
                else:
                    # remove else set and move
                    if 'remove' in itemValues:
                        self.removeItem(item)
                    else:
                        item.setValues(itemValues)
                        self.addItem(item, i)

        if "defaultItem" in data:
            self.setDefaultItem(data.get("defaultItem", None))
        if "inputType" in data:
            self._inputType = data.get("inputType")
        if "emptyCaption" in data:
            self._emptyCaption = data["emptyCaption"]

    def _beforeValueChange(self, item, newItem):
        # if the item had a quantity, make the place available again
        selected = self.getSelectedItem(item)
        if not newItem and selected:
            selected.decreaseNoPlaces()

    def _afterValueChange(self, item):
        # if the item has a quantity now, make the place unavailable
        selected = self.getSelectedItem(item)
        if selected:
            selected.increaseNoPlaces()

    def getSelectedItem(self, item):
        for val in self.getItemsList():
            if val.getCaption() == item.getValue():
                return val
        return None

    def getDefaultItem(self):
        try:
            if self._defaultItem:
                pass
        except AttributeError, e:
            self._defaultItem = None
        return self._defaultItem

    def setDefaultItem(self, caption):
        if caption == "":
            self._defaultItem = None
        else:
            self._defaultItem = caption

    def setDefaultItemById(self, id):
        item = self.getItemById(id)
        if item in self.getItemsList():
            self.setDefaultItem(item.getCaption())

    def changeItemById(self, id, caption=None, billable=None, price=None, places=None):
        item = self.getItemById(id)
        if item in self.getItemsList():
            if caption:
                item.setCaption(caption)
            if billable and price:
                item.setBillable(billable)
                item.setPrice(price)
            if places or places == 0: # empty string doesn't change it, 0 does
                item.setPlacesLimit(places)

    def removePriceById(self, id):
        item = self.getItemById(id)
        if item in self.getItemsList():
            item.setBillable(False)
            item.setPrice("")

    def setInputType(self, inputType):
        self._inputType = inputType

    def getInputType(self):
        try:
            if self._inputType:
                pass
        except AttributeError:
            self._inputType = "radiogroup"
        return self._inputType

    def getItemsList(self):
        if type(self._items) == dict:
            self._items = self._items.values()
        return self._items

    def addItem(self, item, i=None):
        if i is None:
            i = len(self.getItemsList())
        if item in self.getItemsList():
            self.removeItem(item)
        else:
            item.setId(str(self._getRadioItemGenerator().newCount()))

        self.getItemsList().insert(i, item)
        self.notifyModification()
        return True

    def createItem(self, itemValues, i=None):
        item = RadioItem(self)
        item.setValues(itemValues)
        self.addItem(item, i)

    def removeItem(self, item):
        if item in self.getItemsList():
            self.getItemsList().remove(item)
            self.notifyModification()

    def removeItemById(self, id):
        return self.removeItem(self.getItemById(id))

    def disableItemById(self, id):
        item = self.getItemById(id)
        if item in self.getItemsList():
            item.setEnabled(not item.isEnabled())
            self.notifyModification()

    def getItemById(self, id):
        for f in self.getItemsList():
            if f.getId() == id:
                return f
        return None

    def notifyModification(self):
        self._p_changed = 1

    def clone(self, gf):
        rgi = FieldInputType.clone(self, gf)
        for item in self.getItemsList():
            rgi.addItem(item.clone(rgi))
        rgi.setDefaultItem(self.getDefaultItem())
        rgi.setInputType(self.getInputType())
        return rgi

    def _getRadioItemGenerator(self):
        return self._radioItemGenerator

    def getEmptyCaption(self):
        try:
            return self._emptyCaption
        except:
            self._emptyCaption = '-- Choose a value --'
            return self._emptyCaption

    def _getRadioGroupModifHTML(self, item, registrant, default=""):
        description = self._parent.getDescription()
        caption = self._parent.getCaption()
        billable = self._parent.isBillable()
        currency = self._parent.getParent().getRegistrationForm().getCurrency()
        value = default
        if item is not None:
            billable = item.isBillable()
            currency = item.getCurrency()
            value = item.getValue()

        tmp = ["""<td align="right" align="bottom" colspan="2"></td>"""]

        counter = 0
        for val in self.getItemsList():
            counter += 1
            itemId = "%s_%s" % (self.getHTMLName(), counter)
            disable = ""
            if not val.isEnabled():
                disable = "disabled=\"disabled\""
            if (registrant is not None and (val.isBillable() or billable) and registrant.getPayed()):
                disable = "disabled=\"disabled\""
            elif (not val.hasAvailablePlaces() and val.getCaption() != value):
                disable = "disabled=\"disabled\""
            checked = ""
            if val.getCaption() == value:
                checked = "checked"
            elif not value and val.getCaption() == self.getDefaultItem():
                checked = "checked"
            tmp.append("""<tr><td></td><td><input type="radio" id="%s" name="%s" value="%s" %s %s> %s</td><td align="right" style="vertical-align: bottom;" >""" % (itemId, self.getHTMLName(), val.getId(), checked, disable, val.getCaption()))
            if val.isBillable():
                tmp.append("""&nbsp;&nbsp;%s&nbsp;%s""" % (val.getPrice(), currency))
            tmp.append("""</td><td align="right" style="vertical-align: bottom;" >""")
            if val.getPlacesLimit():
                tmp.append("""&nbsp;<span class='placesLeft'>[%s place(s) left]</span>""" % (val.getNoPlacesLeft()))
            tmp.append(""" </td></tr> """)

        if description:
            tmp.append("""<tr><td></td><td colspan="2">%s</td></tr>""" % (self._getDescriptionHTML(description)))

        if self._parent.isMandatory():
            validator = """
            for (var i=1; i<=%s; i++) {
                var item = $E('%s_' + i);
                if (item.dom.checked) {
                  return true;
                }
            }
            new AlertPopup($T("Warning"), $T('You must select option for "%s"!')).open();
            return false;
            """ % (counter, self.getHTMLName(), caption)
            script = """<script>addValidator(function() {%s});</script>""" % validator
            tmp.append(script)

        return "".join(tmp)

    def _getDropDownModifHTML(self, item, registrant, default=""):
        description = self._parent.getDescription()
        billable = self._parent.isBillable()
        currency = self._parent.getParent().getRegistrationForm().getCurrency()
        value = default
        if item is not None:
            billable = item.isBillable()
            currency = item.getCurrency()
            value = item.getValue()

        if not value:
            value = self.getDefaultItem()

        if self._parent.isMandatory():
            param = """<script>addParam($E('%s'), 'text', false);</script>""" % self.getHTMLName()
        else:
            param = ''

        tmp = []
        tmp.append("""<td><select id="%s" name="%s">""" % (self.getHTMLName(), self.getHTMLName()))

        tmp.append("""<option value="">%s</option>""" % self.getEmptyCaption())

        for radioItem in self.getItemsList():
            if radioItem.isEnabled() and not (registrant is not None and (radioItem.isBillable() or billable) and registrant.getPayed()):

                placesInfo = ""
                if radioItem.getPlacesLimit():
                    placesInfo = """&nbsp;[%s place(s) left]""" % (radioItem.getNoPlacesLeft())

                disabled = ""
                if (not radioItem.hasAvailablePlaces() and radioItem.getCaption() != value):
                    disabled = " disabled='disabled'"

                selected = ""
                if radioItem.getCaption() == value:
                    selected = " selected='selected'"
                else:
                    selected = ''

                if radioItem.isBillable():
                    price = """&nbsp;&nbsp;%s&nbsp;%s """ % (radioItem.getPrice(), currency)
                else:
                    price = ''

                tmp.append("""<option value="%s"%s%s>%s%s%s</option>""" % (radioItem.getId(), selected, disabled, radioItem.getCaption(), price, placesInfo))

        tmp.append("""</select>%s</td>""" % param)

        if description:
            tmp.append("""<tr><td colspan="2">%s</td></tr>""" % (self._getDescriptionHTML(description)))

        return "".join(tmp)

    def _getModifHTML(self, item, registrant, default=""):
        if self.getInputType() == 'radiogroup':
            return self._getRadioGroupModifHTML(item, registrant, default)
        else:
            return self._getDropDownModifHTML(item, registrant, default)

    def _setResponseValue(self, item, params, registrant, override=False, validate=True):
        radioitemid = params.get(self.getHTMLName(), "")
        billable = False
        for val in self.getItemsList():
            if val.isBillable():
                billable = True
        if (registrant is not None and self._parent.isBillable() and registrant.getPayed()):
            #if (item is not None and billable):
            #######################
            # if the registrant has already payed, Indico blocks all the modifications about new/removed items
            return
        if not override and self.getParent().isMandatory() and radioitemid.strip() == "":
            raise FormValuesError(_("The field \"%s\" is mandatory. Please fill it.") % self.getParent().getCaption())
        price = 0
        quantity = 0
        caption = ""
        if radioitemid.strip() != "":
            radioitem = self.getItemById(radioitemid)
            if radioitem is not None:
                caption = radioitem.getCaption()
                billable = radioitem.isBillable()
                price = radioitem.getPrice()
                quantity = 1

        item.setCurrency(self._parent.getParent().getRegistrationForm().getCurrency())
        item.setMandatory(self.getParent().isMandatory())
        item.setValue(caption)
        item.setBillable(billable)
        item.setPrice(price)
        item.setQuantity(quantity)
        item.setHTMLName(self.getHTMLName())

    def _getSpecialOptionsHTML(self):
        if self.getInputType() == 'radiogroup':
            radioSelected = ' selected="selected"'
            dropdownSelected = ''
        else:
            radioSelected = ''
            dropdownSelected = ' selected="selected"'
        if self.getParent().isLocked('input'):
            typeDisabled = ' disabled="disabled"'
        else:
            typeDisabled = ''
        html = [i18nformat("""
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">_("Type of input")</span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
              <select name="inputtype"%(typeDisabled)s>
                <option value="radiogroup"%(radioSelected)s>Radio group</option>
                <option value="dropdown"%(dropdownSelected)s>Drop-down menu</option>
              </select>
          </td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">Items</span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
                <table>""") % dict(radioSelected=radioSelected, dropdownSelected=dropdownSelected, typeDisabled=typeDisabled)]
        html.append(i18nformat("""<tr>
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
                            <tr>
                                <td class="blacktext"><span class="titleCellFormat"> _("Places")</span></td>
                                <td bgcolor="white" class="blacktext" width="100%%">
                                    <input type="text" name="newplaces">%s
                                </td>
                            </tr>
                            </table>
                            </td>
                            <td rowspan="2" valign="top" align="left">
                                <input type="submit" class="btn" name="addradioitem" value="_("add")" onfocus="addIsFocused = true;" onblur="addIsFocused = false;"><br>
                                <input type="submit" class="btn" name="removeradioitem" value="_("remove")"><br>
                                <input type="submit" class="btn" name="disableradioitem" value="_("enable/disable")"><br>
                                <input type="submit" class="btn" name="defaultradioitem" value="_("set as default")"><br>
                                <input type="submit" class="btn" name="changeradioitem" value="_("change")"><br>
                                <input type="submit" class="btn" name="removeradioitemprice" value="_("remove price")"><br>
                            </td>
                        </tr>
                """) % inlineContextHelp(_('Use 0 for unlimited places')))
        html.append("""<tr><td valign="top" align="left"><table>""")
        billable = False
        for v in self.getItemsList():
            placesInfo = ""
            if v.getPlacesLimit():
                placesInfo = " (%s places)" % (v.getPlacesLimit())
            html.append("""
                        <tr>
                            <td bgcolor="white" class="blacktext" ><input type="checkbox" name="radioitems" value="%s">%s%s</td>
                            <td bgcolor="white" class="blacktext" >
                        """ % (v.getId(), v.getCaption(), placesInfo))
            if v.isBillable():
                billable = True
                html.append(i18nformat("""<span class="titleCellFormat">&nbsp;&nbsp; _("Price"):%s</span>""") % (v.getPrice()))
            if not v.isEnabled():
                html.append("""<span><font color="red">&nbsp;&nbsp;(""" + _("disabled") + """)</font></span>""")
            if v.getCaption() == self.getDefaultItem():
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


class CountryInput(FieldInputType, Fossilizable):

    fossilizes(IRegFormCountryInputFieldFossil)

    _id = "country"

    def getName(cls):
        return "Country"
    getName = classmethod(getName)

    def getValueDisplay(self, value):
        return CountryHolder().getCountryById(value)

    def getCountriesList(self):
        countryList = []
        for countryKey in CountryHolder().getCountrySortedKeys():
            country = {}
            country["countryKey"] = countryKey
            country["caption"] = CountryHolder().getCountryById(countryKey)
            countryList.append(country)
        return countryList

    def _getModifHTML(self, item, registrant, default=""):
        description = self._parent.getDescription()
        htmlName = self.getHTMLName()
        value = default
        if item is not None:
            value = item.getValue()
            htmlName = item.getHTMLName()
        disable = ""

        if self._parent.isMandatory():
            param = """<script>addParam($E('%s'), 'text', false);</script>""" % htmlName
        else:
            param = ''

        inputHTML = i18nformat("""<option value="">--  _("Select a country") --</option>""")
        for countryKey in CountryHolder().getCountrySortedKeys():
            selected = ""
            if value == countryKey:
                selected = "selected"
            inputHTML += """<option value="%s" %s>%s</option>""" % (countryKey, selected, CountryHolder().getCountryById(countryKey))
        inputHTML = """<select id="%s" name="%s" %s>%s</select>%s""" % (htmlName, htmlName, disable, inputHTML, param)

        tmp = """ <td>%s</td>""" % inputHTML
        if description:
            tmp = """%s</tr><tr><td colspan="2">%s</td>""" % (tmp, self._getDescriptionHTML(description))
        return tmp

    def _setResponseValue(self, item, params, registrant, override=False, validate=True):
        v = params.get(self.getHTMLName(), "")
        if not override and self.getParent().isMandatory() and v.strip() == "":
            raise FormValuesError(_("The field \"%s\" is mandatory. Please fill it.") % self.getParent().getCaption())

        item.setQuantity(0)
        item.setValue(v)
        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())

    def _getSpecialOptionsHTML(self):
        return ""


class DateInput(FieldInputType, Fossilizable):

    fossilizes(IRegFormDateInputFieldFossil)

    _id = "date"

    def __init__(self, field):
        FieldInputType.__init__(self, field)
        self.dateFormat = ''

    def getName(cls):
        return "Date"
    getName = classmethod(getName)

    def getValues(self):
        d = {}
        d["dateFormat"] = self.getDateFormat()
        return d

    def setValues(self, data):
        if data.has_key("dateFormat"):
            self.setDateFormat(data.get("dateFormat"))

    def clone(self, gf):
        di = FieldInputType.clone(self, gf)
        di.dateFormat = self.getDateFormat()
        return di

    def getDateFormat(self):
        if self.dateFormat == '':
            self.dateFormat = self.getDisplayFormats()[0][0]
        return self.dateFormat

    def setDateFormat(self, dateFormat):
        self.dateFormat = dateFormat

    def getDisplayFormats(self):
        return [('%d/%m/%Y %H:%M', 'DD/MM/YYYY hh:mm'),
                   ('%d.%m.%Y %H:%M', 'DD.MM.YYYY hh:mm'),
                   ('%m/%d/%Y %H:%M', 'MM/DD/YYYY hh:mm'),
                   ('%m.%d.%Y %H:%M', 'MM.DD.YYYY hh:mm'),
                   ('%Y/%m/%d %H:%M', 'YYYY/MM/DD hh:mm'),
                   ('%Y.%m.%d %H:%M', 'YYYY.MM.DD hh:mm'),
                   ('%d/%m/%Y', 'DD/MM/YYYY'),
                   ('%d.%m.%Y', 'DD.MM.YYYY'),
                   ('%m/%d/%Y', 'MM/DD/YYYY'),
                   ('%m.%d.%Y', 'MM.DD.YYYY'),
                   ('%Y/%m/%d', 'YYYY/MM/DD'),
                   ('%Y.%m.%d', 'YYYY.MM.DD'),
                   ('%m/%Y', 'MM/YYYY'),
                   ('%m.%Y', 'MM.YYYY'),
                   ('%Y', 'YYYY')]

    def getValueDisplay(self, value):
        if type(value) == datetime:
            return value.strftime(self.getDateFormat())
        else:
            return value

    def getHTMLName(self):
        return "_genfield_%s_%s_" % (self.getParent().getParent().getId(), self.getParent().getId())

    def _getModifHTML(self, item, registrant, default=""):
        description = self._parent.getDescription()
        if item is not None:
            date = item.getValue()
            htmlName = item.getHTMLName()
        else:
            date = default or None
            htmlName = self.getHTMLName()

        from MaKaC.webinterface.wcomponents import WDateField
        inputHTML = WDateField(htmlName, date, self.getDateFormat(), True, self._parent.isMandatory()).getHTML()

        dateFormat = self.getDateFormat()
        dateFormat = re.sub('%d', 'DD', dateFormat)
        dateFormat = re.sub('%m', 'MM', dateFormat)
        dateFormat = re.sub('%Y', 'YYYY', dateFormat)
        dateFormat = re.sub('%H', 'hh', dateFormat)
        dateFormat = re.sub('%M', 'mm', dateFormat)

        dformat = """&nbsp;<span class="inputDescription">%s</span>""" % dateFormat
        tmp = "%s %s" % (inputHTML, dformat)
        tmp = """ <td>%s</td><td align="right" align="bottom">""" % tmp
        tmp = """%s </td> """ % tmp
        if description:
            tmp = """%s</tr><tr><td>%s</td>""" % (tmp, self._getDescriptionHTML(description))
        return tmp

    def _setResponseValue(self, item, params, registrant, override=False, validate=True):
        day = params.get('%sDay' % self.getHTMLName(), 1) or 1
        month = params.get('%sMonth' % self.getHTMLName(), 1) or 1
        year = params.get('%sYear' % self.getHTMLName())

        hour = params.get('%sHour' % self.getHTMLName(), 0) or 0
        minute = params.get('%sMin' % self.getHTMLName(), 0) or 0

        if year:
            date = datetime(int(year), int(month), int(day), int(hour), int(minute))
            item.setValue(date)
        elif not self._parent.isMandatory():
            item.setValue(None)
        elif not override:
            raise FormValuesError(_("The field \"%s\" is mandatory. Please fill it.") % self.getParent().getCaption())

        item.setMandatory(self.getParent().isMandatory())
        item.setHTMLName(self.getHTMLName())

    def _getSpecialOptionsHTML(self):
        formats = self.getDisplayFormats()

        html = [i18nformat("""
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">_("Date format")</span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
              <select name="dateFormat">""")]

        for format, display in formats:
            if self.getDateFormat() == format:
                selected = ' selected="selected"'
            else:
                selected = ''
            html.append("""<option value="%s"%s>%s</option>""" % (format, selected, display))

        html.append(_("""</select>
          </td>
        </tr>"""))
        return "".join(html)

    def _getFormatDisplayText(self):
        formats = self.getDisplayFormats()

        value = ""
        for dateFormat, display in formats:
            if self.getDateFormat() == dateFormat:
                value = display
                break
        return value


class FieldInputs:

    _availableInputs = {TextInput.getId():TextInput, \
                      TextareaInput.getId(): TextareaInput, \
                      LabelInput.getId():LabelInput, \
                      NumberInput.getId():NumberInput, \
                      RadioGroupInput.getId():RadioGroupInput, \
                      CheckboxInput.getId():CheckboxInput, \
                      YesNoInput.getId(): YesNoInput, \
                      CountryInput.getId(): CountryInput, \
                      DateInput.getId(): DateInput, \
                      TelephoneInput.getId(): TelephoneInput, \
                      FileInput.getId(): FileInput
                     }

    def getAvailableInputs(cls):
        return cls._availableInputs
    getAvailableInputs = classmethod(getAvailableInputs)

    def getAvailableInputKlassById(cls, id):
        return cls._availableInputs.get(id, None)
    getAvailableInputKlassById = classmethod(getAvailableInputKlassById)

    def getAvailableInputKeys(cls):
        return cls._availableInputs.keys()
    getAvailableInputKeys = classmethod(getAvailableInputKeys)


class GeneralField(Persistent, Fossilizable):

    fossilizes(IRegFormGeneralFieldFossil)

    def __init__(self, parent, data=None):
        self._parent = parent
        self._id = ""
        if data is None:
            self._caption = "General Field"
            self._input = FieldInputs.getAvailableInputKlassById("text")(self)
            self._input.setValues(data)
            self._mandatory = False
            self._locked = ()
            self._description = ""
            self._billable = False
            self._price = "0"
            self._placesLimit = 0
            self._currentNoPlaces = 0
            self._disabled = True
            self._pdField = None
        else:
            self._mandatory = False
            self.setValues(data, True)

    def clone(self, newsection):
        field = GeneralField(newsection, self.getValues())
        return field

    def setValues(self, data, firstTime=False):
        caption = data.get("caption", "")
        if caption == "":
            caption = _("General Field")
        self.setCaption(caption)
        ## The following commented lines were removed, but it is unclear if they are not needed anymore.
        if firstTime: # or not self.isLocked('input'):
            self.setInput(FieldInputs.getAvailableInputKlassById(data.get("input", "text"))(self))
        #else:
        #    self.setInput(FieldInputs.getAvailableInputKlassById(self.getInput().getId())(self))
        if data.has_key("inputObj"):
            self._input.setValues(data["inputObj"].getValues())
        elif data.has_key('inputValues'):
            self._input.setValues(data["inputValues"])
        else:
            self._input.setValues(data)
        if firstTime:
            self.setLocked(data.get("lock", ()))
        if self.isMandatory() and self.isLocked('mandatory'):
            self.setMandatory(True)
        else:
            self.setMandatory(data['mandatory'] if 'mandatory' in data else False)
        if self.isLocked('disable'):
            self.setDisabled(False)
        elif 'disabled' in data:
            self.setDisabled(data.get("disabled", False))
        self.setBillable(data.get("billable", False))
        self.setPrice(str(data.get("price", "")))
        self.setPlacesLimit(data.get("placesLimit", "0"))
        self.setDescription(data.get("description", ""))
        if firstTime:
            self.setPDField(data.get("pd"))

    def getValues(self):
        values = {}
        values["caption"] = self.getCaption()
        values["input"] = self.getInput().getId()
        values["inputObj"] = self.getInput()
        values["lock"] = self.getLocked()
        values["mandatory"] = self.isMandatory()
        values["disabled"] = self.isDisabled()
        values["billable"] = self.isBillable()
        values["price"] = self.getPrice()
        values["placesLimit"] = self.getPlacesLimit()
        values["description"] = self.getDescription()
        values["pd"] = self.getPDField()
        return values

    def isTemporary(self):
        return False

    def setPDField(self, v):
        self._pdField = v

    def getPDField(self):
        try:
            return self._pdField
        except:
            self._pdField = None
            return self._pdField

    def isBillable(self):
        try:
            return self._billable
        except:
            self._billable = False
        return self._billable

    def setBillable(self, v):
        self._billable = v

    def getPrice(self):
        try:
            return self._price
        except:
            self._price = 0
        return self._price

    def setPrice(self, price):
        if price:
            match = PRICE_PATTERN.match(price)
            if match:
                price = match.group(1)
            else:
                raise MaKaCError(_('The price is in incorrect format!'))
        self._price = price

    def getPlacesLimit(self):
        try:
            if self._placesLimit:
                pass
        except AttributeError, e:
            self._placesLimit = 0
        return self._placesLimit

    def setPlacesLimit(self, limit):
        if limit == "":
            limit = "0"
        try:
            l = int(limit)
        except ValueError:
            raise FormValuesError(_("Please enter a number for the limit of places"))
        self._placesLimit = l
        self.updateCurrentNoPlaces()

    def getCurrentNoPlaces(self):
        try:
            if self._currentNoPlaces:
                pass
        except AttributeError:
            self._currentNoPlaces = 0
        return self._currentNoPlaces

    def hasAvailablePlaces(self):
        if not self.getPlacesLimit():
            return True
        return (self.getCurrentNoPlaces() < self.getPlacesLimit())

    def getNoPlacesLeft(self):
        return self.getPlacesLimit() - self.getCurrentNoPlaces()

    def increaseNoPlaces(self):
        if self.getPlacesLimit() > 0:
            if self.getCurrentNoPlaces() >= self.getPlacesLimit():
                raise FormValuesError(_("""The limit for the number of places is smaller than the current amount registered for this item."""))
            self._currentNoPlaces += 1

    def decreaseNoPlaces(self):
        if self.getPlacesLimit() > 0 and self.getCurrentNoPlaces() > 0:
            self._currentNoPlaces -= 1

    def updateCurrentNoPlaces(self):
        self._currentNoPlaces = 0

        if self._parent.getId() == '':
            # parent is not yet in the form
            return

        for reg in self._parent.getRegistrationForm().getConference().getRegistrantsList():
            mg = reg.getMiscellaneousGroupById(self._parent.getId())
            if mg:
                item = mg.getResponseItemById(self.getId())
                if item is not None and item.getQuantity():
                    self.increaseNoPlaces()

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getCaption(self):
        return self._caption

    def setCaption(self, caption):
        self._caption = caption

    def getDescription(self):
        try:
            if self._description:
                pass
        except AttributeError:
            self._description = ''
        return self._description

    def setDescription(self, description):
        self._description = description

    def getInput(self):
        return self._input

    def setInput(self, input):
        self._input = input

    def isMandatory(self):
        return self._mandatory

    def setMandatory(self, v):
        self._mandatory = v

    def getLocked(self):
        try:
            return self._locked
        except:
            self._locked = ()
            return self._locked

    def isLocked(self, what):
        return what in self.getLocked()

    def setLocked(self, v):
        self._locked = v

    def isDisabled(self):
        try:
            return self._disabled
        except:
            self._disabled = False
            return self._disabled

    def setDisabled(self, v):
        self._disabled = v

    def getParent(self):
        return self._parent

    def getLocator(self):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the GeneralField instance """
        if self.getParent() == None:
            return Locator()
        lconf = self.getParent().getLocator()
        lconf["sectionFieldId"] = self.getId()
        return lconf


class GeneralSectionForm(BaseForm, Fossilizable):

    fossilizes(IRegFormGeneralSectionFossil)

    def __init__(self, regForm, data=None, required=False):
        BaseForm.__init__(self)
        self._regForm = regForm
        self._id = ""
        self._title = _("Miscellaneous information")
        self._description = ""
        self._required = required

        #####
        #Mods to support sorting fields
        #self._fields=[]

        self._sortedFields = []

        if data is not None:
            self._title = data.get("title", self._title)
            self._description = data.get("description", self._description)
        self._generalFieldGenerator = Counter()

    def setValues(self, data):
        title = data.get("title", "").strip()
        if title == "":
            title = _("Miscellaneous information %s") % self.getId()
        self.setTitle(title)
        self.setDescription(data.get("description", ""))
        if 'required' in data:
            self.setRequired(data['required'])

    def getValues(self):
        values = {}
        values["title"] = self.getTitle()
        values["description"] = self.getDescription()
        values["enabled"] = self.isEnabled()
        values["required"] = self.isRequired()
        return values

    def clone(self, regForm):
        gsf = GeneralSectionForm(regForm)
        gsf.setId(self.getId())
        gsf.setValues(self.getValues())
        gsf.setEnabled(self.isEnabled())
        gsf.setRequired(self.isRequired())

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

    def setDescription(self, description):
        self._description = description

    def isRequired(self):
        try:
            return self._required
        except:
            self._required = False
            return False

    def setRequired(self, required):
        self._required = required

    def getSortedFields(self):
        try:
           returnFields = self._sortedFields
        except AttributeError:
           self._sortedFields = self._fields
           returnFields = self._sortedFields
        return returnFields

    def addToSortedFields(self, f, i=None):
        if i is None:
            i = len(self.getSortedFields())
        try:
            self.getSortedFields().remove(f)
        except ValueError, e:
            f.setId(str(self._getGeneralFieldGenerator().newCount()))
        self.getSortedFields().insert(i, f)
        self.notifyModification()
        return True

    def removeField(self, f):
        if f in self.getSortedFields():
            self.getSortedFields().remove(f)
            self.notifyModification()

    def getFieldById(self, id):
        for f in self.getSortedFields():
            if f.getId() == id:
               return f
        return None

    def getFieldPosById(self, id):
        for ind, f in enumerate(self.getSortedFields()):
            if f.getId() == id:
               return ind
        return None
    #
    #end mods
    ##########

    def getLocator(self):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the GeneralSectionForm instance """
        if self.getRegistrationForm().getConference() == None:
            return Locator()
        lconf = self.getRegistrationForm().getLocator()
        lconf["sectionFormId"] = self.getId()
        return lconf

    def notifyModification(self):
        self._p_changed = 1


class PersonalDataForm(GeneralSectionForm):
    def __init__(self, regForm, createFields=True):
        GeneralSectionForm.__init__(self, regForm, {'title': 'Personal Data'}, True)

        fields = (
            { 'pd': 'title',
              'caption': 'Title',
              'input': 'radio',
              'inputValues': {
                  'inputType':'dropdown',
                  'emptyCaption': '',
                  'radioitems': [{'caption':title} for title in TitlesRegistry.getList()]
              },
              'lock': ('input', 'delete')
            },
            { 'pd':'firstName', 'caption':'First Name', 'mandatory':True, 'lock':('mandatory', 'input', 'delete', 'disable') },
            { 'pd':'surname', 'caption':'Surname', 'mandatory':True, 'lock':('mandatory', 'input', 'delete', 'disable') },
            { 'pd':'position', 'caption':'Position', 'lock':('input', 'delete') },
            { 'pd':'institution', 'caption':'Institution', 'mandatory':True, 'lock':('input', 'delete') },
            { 'pd':'address', 'caption':'Address', 'lock':('input', 'delete') },
            { 'pd':'city', 'caption':'City', 'mandatory':True, 'lock':('input', 'delete') },
            { 'pd':'country', 'caption':'Country', 'input':'country', 'mandatory':True, 'lock':('input', 'delete') },
            { 'pd':'phone', 'caption':'Phone', 'input':'telephone', 'lock':('input', 'delete') },
            { 'pd':'fax', 'caption':'Fax', 'input':'telephone', 'lock':('input', 'delete') },
            { 'pd':'email', 'caption':'Email', 'mandatory':True, 'lock':('mandatory', 'input', 'delete', 'disable') },
            { 'pd':'personalHomepage', 'caption':'Personal homepage', 'lock':('input', 'delete') },
        )

        self._pdMap = {}
        if createFields:
            for fieldInfo in fields:
                field = GeneralField(self, fieldInfo)
                self._pdMap[fieldInfo['pd']] = field
                self.addToSortedFields(field)

    def clone(self, regForm):
        pf = PersonalDataForm(regForm, False)
        pf.setId(self.getId())
        pf.setValues(self.getValues())
        pf.setEnabled(self.isEnabled())
        pf.setRequired(self.isRequired())
        for field in self.getSortedFields():
            f = field.clone(pf)
            pf.addToSortedFields(f)
            if f.getPDField():
                pf._pdMap[f.getPDField()] = f
        return pf

    def getValueFromParams(self, params, field):
        return params.get(self._pdMap[field].getInput().getHTMLName())

    def getField(self, field):
        return self._pdMap[field]

    def getRegistrantValues(self, registrant):
        mg = registrant.getMiscellaneousGroupById(self.getId())
        return dict((name, mg.getResponseItemById(field.getId()).getValue()) for name, field in self._pdMap.iteritems() if not field.isDisabled())

    def getValuesFromAvatar(self, av):
        r = dict((k, '') for k in ['title', 'firstName', 'surname', 'institution',
                                   'email', 'address', 'phone', 'fax'])
        if av is not None:
            r['title'] = av.getTitle()
            r['firstName'] = av.getFirstName()
            r['surname'] = av.getFamilyName()
            r['institution'] = av.getOrganisation()
            r['email'] = av.getEmail()
            r['address'] = av.getAddress()
            r['phone'] = av.getTelephone()
            faxes = av.getFaxes()
            fax = ''
            if len(faxes) > 0:
                fax = faxes[0]
            r['fax'] = fax
        return r

    def getFormValuesFromAvatar(self, av):
        r = {}

        if av is not None:
            r[self._pdMap['title'].getInput().getHTMLName()] = av.getTitle()
            r[self._pdMap['firstName'].getInput().getHTMLName()] = av.getFirstName()
            r[self._pdMap['surname'].getInput().getHTMLName()] = av.getFamilyName()
            r[self._pdMap['institution'].getInput().getHTMLName()] = av.getOrganisation()
            r[self._pdMap['email'].getInput().getHTMLName()] = av.getEmail()
            r[self._pdMap['address'].getInput().getHTMLName()] = av.getAddress()
            r[self._pdMap['phone'].getInput().getHTMLName()] = av.getTelephone()
            faxes = av.getFaxes()
            fax = ''
            if len(faxes) > 0:
                fax = faxes[0]
            r[self._pdMap['fax'].getInput().getHTMLName()] = fax
        return r

    def getValuesFromRegistrant(self, reg):
        r = {}
        r['title'] = reg.getTitle()
        r['firstName'] = reg.getFirstName()
        r['surname'] = reg.getFamilyName()
        r['position'] = reg.getPosition()
        r['institution'] = reg.getInstitution()
        r['address'] = reg.getAddress()
        r['city'] = reg.getCity()
        r['country'] = reg.getCountry()
        r['phone'] = reg.getPhone()
        r['fax'] = reg.getFax()
        r['email'] = reg.getEmail()
        r['personalHomepage'] = reg.getPersonalHomepage()
        return r


class PersonalDataFormItem(Persistent): # old

    def __init__(self, data=None):
        if data is None:
            self._id = ""
            self._name = ""
            self._input = ""
            self._mandatory = False
            self._enabled = True
        else:
            self._id = data.get("id", "")
            self._name = data.get("name", "")
            self._input = data.get("input", "")
            self._mandatory = data.get("mandatory", False)
            self._enabled = data.get("enabled", True)

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
        p = PersonalDataFormItem({'id':'title', 'name': "Title", 'input':'list', 'mandatory':False})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'firstName', 'name': "First Name", 'input':'text', 'mandatory':True})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'surname', 'name': "Surname", 'input':'text', 'mandatory':True})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'position', 'name': "Position", 'input':'text', 'mandatory':False})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'institution', 'name': "Institution", 'input':'text', 'mandatory':True})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'address', 'name': "Address", 'input':'text', 'mandatory':False})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'city', 'name': "City", 'input':'text', 'mandatory':True})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'country', 'name': "Country/Region", 'input':'list', 'mandatory':True})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'phone', 'name': "Phone", 'input':'text', 'mandatory':False})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'fax', 'name': "Fax", 'input':'text', 'mandatory':False})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'email', 'name': "Email", 'input':'hidden', 'mandatory':True})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())
        p = PersonalDataFormItem({'id':'personalHomepage', 'name': "Personal homepage", 'input':'text', 'mandatory':False})
        self._data[p.getId()] = p
        self._sortedKeys.append(p.getId())

    def clone(self):
        form = PersonalData()
        for key, item in self._data.iteritems():
            newItem = form.getDataItem(key)
            newItem.setEnabled(item.isEnabled())
            newItem.setMandatory(item.isMandatory())
        return form

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
            if len(faxes) > 0:
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


class FurtherInformationForm(BaseForm, Fossilizable):

    fossilizes(IRegFormFurtherInformationSectionFossil)

    def __init__(self, data=None):
        BaseForm.__init__(self)
        self._title = "Further information"
        self._content = ""
        if data is not None:
            self._title = data.get("title", self._title)
            self._content = data.get("content", self._content)
        self._id = "furtherInformation"

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id = "furtherInformation"
        return self._id

    def setValues(self, data):
        self.setTitle(data.get("title", "Further Information"))
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

    def setContent(self, content):
        self._content = content

    # Fallback for setDescription
    setDescription = setContent

    def getItems(self):
        return ""


class AccommodationType(Persistent, Fossilizable):

    fossilizes(IRegFormAccommodationTypeItemFossil)

    def __init__(self, rf, data=None):
        self._id = ""
        self._caption = ""
        self._regForm = rf
        self._cancelled = False
        self._placesLimit = 0
        self._currentNoPlaces = 0
        self._billable = False
        self._price = 0

    def setValues(self, data):
        self.setCaption(data.get("caption", "--no caption--"))
        self.setCancelled(data.has_key("cancelled") and data["cancelled"])
        self.setPlacesLimit(data.get("placesLimit", "0"))
        self.setBillable(data.has_key("billable") and data["billable"])
        self.setPrice(data.get("price"))
        self._regForm.notifyModification()

    def getValues(self):
        values = {}
        values["caption"] = self.getCaption()
        if self.isCancelled():
            values["cancelled"] = self.isCancelled()
        values["placesLimit"] = self.getPlacesLimit()
        if self.isBillable():
            values["billable"] = True
        values["price"] = self.getPrice()

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
        if limit == "":
            limit = "0"
        try:
            l = int(limit)
        except ValueError, e:
            raise FormValuesError(_("Please introduce a number for the limit of places"))
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
        if self.getPlacesLimit() == 0: #zero means no limit
            return True
        if self.getCurrentNoPlaces() >= self.getPlacesLimit():
            return False
        return True

    def getNoPlacesLeft(self):
        return self.getPlacesLimit() - self.getCurrentNoPlaces()

    def increaseNoPlaces(self):
        if self.getPlacesLimit() > 0 :
            if self.getCurrentNoPlaces() >= self.getPlacesLimit():
                raise FormValuesError(_("""The limit for the number of places is smaller than the current amount registered for this accommodation. Please, set a higher limit."""))
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

    def isBillable(self):
        try:
            return self._billable
        except:
            self._billable = False
        return self._billable

    def setBillable(self, v):
        self._billable = v

    def getPrice(self):
        try:
            return self._price
        except:
            self.setPrice(0)
        return self._price

    def setPrice(self, price):
        if price:
            match = PRICE_PATTERN.match(price)
            if match:
                price = match.group(1)
            else:
                raise MaKaCError(_('The price is in incorrect format!'))
        self._price = price

    def getCurrency(self):
        return self._regForm.getCurrency()

    def remove(self):
        self.setCancelled(True)
        self.delete()

    def delete(self):
        self.setRegistrationForm(None)
        TrashCanManager().add(self)

    def recover(self, rf):
        self.setRegistrationForm(rf)
        TrashCanManager().remove(self)

    def getLocator(self):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the AccommodationType instance """
        if self.getRegistrationForm().getConference() is None:
            return Locator()
        lconf = self.getRegistrationForm().getLocator()
        lconf["accoTypeId"] = self.getId()
        return lconf


class AccommodationForm(BaseForm, Fossilizable):

    fossilizes(IRegFormAccommodationSectionFossil)

    _iterableContainer = '_accommodationTypes'

    def __init__(self, regForm, data=None):
        BaseForm.__init__(self)
        self._accoTypeGenerator = Counter()
        self._regForm = regForm
        self._title = "Accommodation"
        self._description = ""
        self._accommodationTypes = PersistentMapping()
        if data is not None:
            self._title = data.get("title", self._title)
            self._description = data.get("description", self._description)
        self._setDefaultAccommodationTypes()
        self._id = "accommodation"
        self._arrivalOffsetDates = [-2, 0]
        self._departureOffsetDates = [1, 3]

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id = "accommodation"
        return self._id

    def getConference(self):
        return self._regForm.getConference()

    def getArrivalOffsetDates(self):
        try:
            return self._arrivalOffsetDates
        except:
            self.setDefaultArrivalOffsetDates()
            return self._arrivalOffsetDates

    def setDefaultArrivalOffsetDates(self):
        self._arrivalOffsetDates = [-2, 0]

    def getArrivalDates(self):
        offsets = self.getArrivalOffsetDates()
        conf = self.getConference()
        dates = []
        curDate = startDate = conf.getStartDate() + timedelta(days=offsets[0])
        endDate = conf.getEndDate() + timedelta(days=offsets[1])
        if startDate > endDate:
            endDate = startDate
        while curDate <= endDate:
            dates.append(curDate)
            curDate += timedelta(days=1)
        return dates

    def setArrivalOffsetDates(self, dates):
        self._arrivalOffsetDates = dates

    def getDepartureOffsetDates(self):
        try:
            return self._departureOffsetDates
        except:
            self.setDefaultDepartureOffsetDates()
            return self._departureOffsetDates

    def setDefaultDepartureOffsetDates(self):
        self._departureOffsetDates = [1, 3]

    def getDepartureDates(self):
        offsets = self.getDepartureOffsetDates()
        conf = self.getConference()
        dates = []
        curDate = startDate = conf.getStartDate() + timedelta(days=offsets[0])
        endDate = conf.getEndDate() + timedelta(days=offsets[1])
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
        a.setCaption("CERN Hostel")
        self._accommodationTypes[a.getId()] = a
        a = AccommodationType(self._regForm)
        a.setId("own-accommodation")
        a.setCaption("I will arrange my own accommodation")
        self._accommodationTypes[a.getId()] = a
        a = AccommodationType(self._regForm)
        a.setId("geneva-hotel")
        a.setCaption("I prefer to book a room in a Geneva hotel")
        self._accommodationTypes[a.getId()] = a

    def setValues(self, data):
        self.setTitle(data.get("title", "Accommodation"))
        self.setDescription(data.get("description", ""))
        self.setArrivalOffsetDates([int(data.get("aoffset1", -2)), int(data.get("aoffset2", 0))])
        self.setDepartureOffsetDates([int(data.get("doffset1", 1)), int(data.get("doffset2", 3))])

    def getValues(self):
        values = {}
        values["title"] = self.getTitle()
        values["description"] = self.getDescription()
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

    def getRegistrationForm(self):
        return self._regForm

    def _generateNewAccoTypeId(self):
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


class ReasonParticipationForm(BaseForm, Fossilizable):

    fossilizes(IRegFormReasonParticipationSectionFossil)

    def __init__(self, data=None):
        BaseForm.__init__(self)
        self._title = "Reason for participation"
        self._description = "Please, let us know why you are interested to participate in our event:"
        if data is not None:
            self._title = data.get("title", self._title)
            self._description = data.get("description", self._description)
        self._id = "reasonParticipation"

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id = "reasonParticipation"
        return self._id

    def setValues(self, data):
        self.setTitle(data.get("title", "Reason for participation"))
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

    def getItems(self):
        #No items for this form
        return ""


class RegistrationSession(Persistent, Fossilizable):

    fossilizes(IRegFormRegistrationSessionItemFossil)

    def __init__(self, ses, regForm=None):
        self._session = ses
        self._session.setRegistrationSession(self)
        self._regForm = regForm
        self._price = 0
        self._billable = False
        self._currency = regForm.getCurrency()

    def setValues(self, data):
        self.setBillable(data.has_key("billable") and data["billable"])
        self.setPrice(data.get("price"))

    def getValues(self):
        data = {}
        if self.isBillable():
            data["billable"] = True
        data["price"] = self.getPrice()
        return data

    def getSession(self):
        return self._session

    def setSession(self, ses):
        self._session = ses
        self._billable = ses.isBillable()
        self._price = ses.getPrice()

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

    def getPrice(self):
        try:
            return self._price
        except:
            self.setPrice(0)
        return self._price

    def setPrice(self, price):
        if price:
            match = PRICE_PATTERN.match(price)
            if match:
                price = match.group(1)
            else:
                raise MaKaCError(_('The price is in incorrect format!'))
        self._price = price

    def isBillable(self):
        try:
            return self._billable
        except:
            self._billable = False
        return self._billable

    def setBillable(self, v):
        self._billable = v

    def getCurrency(self):
        if not hasattr(self, "_currency") or not self._currency:
            # it may happen that _regForm doesn't exist (session was removed from it)
            if self._regForm:
                self._currency = self._regForm.getCurrency()
            else:
                self._currency = None
        return self._currency

    def getLocator(self):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the RegistrationSession instance """
        if self.getRegistrationForm().getConference() == None:
            return Locator()
        lconf = self.getRegistrationForm().getLocator()
        lconf["sessionId"] = self.getId()
        return lconf

    @staticmethod
    def _cmpTitle(s1, s2):
        if s1 is None and s2 is not None:
            return -1
        elif s1 is not None and s2 is None:
            return 1
        elif s1 is None and s2 is None:
            return 0
        return cmp(s1.getTitle(), s2.getTitle())


class SessionsForm(BaseForm, Fossilizable):

    fossilizes(IRegFormSessionSectionFossil)

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
        self._id = "sessions"

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id = "sessions"
        return self._id

    def clone(self, newSessions):
        sesf = SessionsForm()
        sesf.setTitle(self.getTitle())
        sesf.setType(self.getType())
        sesf.setDescription(self.getDescription())
        sesf.setEnabled(self.isEnabled())
        for s in newSessions:
            ses = self.getSessionById(s.getId())
            if ses:
                s.setValues(ses.getValues())
            sesf.addSession(s)

        return sesf

    def getValues(self):
        data = {}
        data["title"] = self.getTitle()
        data["description"] = self.getDescription()
        data["enabled"] = self.isEnabled()
        data["type"] = self.getType()
        return data

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
                    raise FormValuesError(_("Please, choose at least one session in order to register"))
                if params.get("session1", "") == params.get("session2", "nosession"):
                    raise FormValuesError(_("You cannot choose the same session twice"))
                sessions.append(self.getSessionById(params.get("session1")))
                ses2 = self.getSessionById(params.get("session2", "nosession"))
                if ses2 is not None:
                    sessions.append(ses2)
            elif self.getType() == "all":
                sess = params.get("sessions", [])
                if type(sess) != list:
                    sess = [sess]
                for ses in sess:
                    if self.hasSession(ses):
                        sessions.append(self.getSessionById(ses))
        return [RegistrantSession(ses) for ses in sessions]

    def getSessionList(self, doSort=False):
        lv = self._sessions.values()
        lv.sort(sortByStartDate)
        if doSort:
            lv.sort(RegistrationSession._cmpTitle)
        return lv

    def getSessions(self):
        return self._sessions

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


def sortByStartDate(x, y):
    return cmp(x.getSession().getStartDate(), y.getSession().getStartDate())


class SocialEventItem(Persistent, Fossilizable):

    fossilizes(IRegFormSocialEventItemFossil)

    def __init__(self, rf, data=None):
        self._id = ""
        self._caption = "--no caption--"
        self._regForm = rf
        self._cancelled = False
        self._cancelledReason = ""
        self._maxPlacePerRegistrant = 10
        self._placesLimit = 0
        self._currentNoPlaces = 0
        self._billable = False
        self._price = 0
        self._pricePerPlace = False

    def setValues(self, data):
        if "caption" in data:
            self.setCaption(data["caption"])
        if "cancelled" in data:
            self.setCancelled(data["cancelled"])
        if "cancelledReason" in data:
            self.setCancelledReason(data["cancelledReason"])
        if "maxPlace" in data:
            try:
                maxPlace = int(data["maxPlace"])
            except ValueError:
                maxPlace = 0
            if maxPlace < 0:
                maxPlace = 0
            self.setMaxPlacePerRegistrant(maxPlace)
        if "placesLimit" in data:
            self.setPlacesLimit(data["placesLimit"])
        if "billable" in data:
            self.setBillable(data["billable"])
        if "billable" in data:
            self.setPricePerPlace(data["pricePerPlace"])
        if "price" in data:
            self.setPrice(data["price"])

    def getValues(self):
        data = {}
        data["caption"] = self.getCaption()
        if self.isCancelled():
            data["cancelled"] = self.isCancelled()
        data["cancelledReason"] = self.getCancelledReason()
        data["maxPlace"] = self.getMaxPlacePerRegistrant()
        data["placesLimit"] = self.getPlacesLimit()
        if self.isBillable():
            data["billable"] = True
        if self.isPricePerPlace():
            data["pricePerPlace"] = True
        data["price"] = self.getPrice()
        return data

    def clone(self, regForm):
        newSEI = SocialEventItem(regForm)
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
        if limit == "":
            limit = "0"
        try:
            l = int(limit)
        except ValueError, e:
            raise FormValuesError(_("Please introduce a number for the limit of places"))
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
            if (self.getCurrentNoPlaces() + n) > self.getPlacesLimit():
                raise FormValuesError(_("We are sorry but there are not enough places for the social event \"%s\". \
                         ") % (self.getCaption()))
            self._currentNoPlaces += n

    def decreaseNoPlaces(self, n):
        if self.getPlacesLimit() > 0 and self.getCurrentNoPlaces() > 0:
            if (self._currentNoPlaces - n) < 0:
                raise FormValuesError(_("Impossible to decrease %s places for \"%s\" because the current number of \
                        places would be less than zero") % (n, self.getCaption()))
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

    def isBillable(self):
        try:
            return self._billable
        except:
            self._billable = False
        return self._billable

    def setBillable(self, v):
        self._billable = v

    def isPricePerPlace(self):
        try:
            return self._pricePerPlace
        except:
            self._pricePerPlace = False
        return self._pricePerPlace

    def setPricePerPlace(self, v):
        self._pricePerPlace = v

    def getPrice(self):
        try:
            return self._price
        except:
            self.setPrice(0)
        return self._price

    def setPrice(self, price):
        if price:
            match = PRICE_PATTERN.match(price)
            if match:
                price = match.group(1)
            else:
                raise MaKaCError(_('The price is in incorrect format!'))
        self._price = price

    def getCurrency(self):
        return self._regForm.getCurrency()

    def remove(self):
        self.setCancelled(True)
        self.delete()

    def delete(self):
        self.setRegistrationForm(None)
        TrashCanManager().add(self)

    def recover(self, rf):
        self.setRegistrationForm(rf)
        TrashCanManager().remove(self)

    def getLocator(self):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the SocialEventItem instance """
        if self.getRegistrationForm().getConference() == None:
            return Locator()
        lconf = self.getRegistrationForm().getLocator()
        lconf["socialEventId"] = self.getId()
        return lconf

    @staticmethod
    def _cmpCaption(se1, se2):
        return cmp(se1.getCaption().lower(), se2.getCaption().lower())


class SocialEventForm(BaseForm, Fossilizable):

    fossilizes(IRegFormSocialEventSectionFossil)

    _iterableContainer = '_socialEvents'

    def __init__(self, regForm, data=None):
        BaseForm.__init__(self)
        self._socialEventItemGenerator = Counter()
        self._regForm = regForm
        self._title = "Social Events"
        self._description = ""
        self._introSentence = self._getDefaultIntroValue()
        self._mandatory = False
        self._selectionType = "multiple"
        self._socialEvents = PersistentMapping()
        if data is not None:
            self._title = data.get("title", self._title)
            self._description = data.get("description", self._description)
            self._mandatory = data.get('mandatory', False)
        self._id = "socialEvents"

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id = "socialEvents"
        return self._id

    def setValues(self, data):
        self.setTitle(data.get("title", "Sessions"))
        self.setDescription(data.get("description", ""))
        self.setIntroSentence(data.get("intro", ""))
        self.setSelectionType(data.get("selectionType", "multiple"))
        self.setMandatory(data.get('mandatory', False))

    def getValues(self):
        values = {}
        values["title"] = self.getTitle()
        values["description"] = self.getDescription()
        values["intro"] = self.getIntroSentence()
        values["selectionType"] = self.getSelectionTypeId()
        values["mandatory"] = self.getMandatory()
        return values

    def clone(self, registrationForm):
        sef = SocialEventForm(registrationForm)
        sef.setValues(self.getValues())
        sef.setEnabled(self.isEnabled())

        for se in self.getSocialEventList():
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

    def getMandatory(self):
        try:
            return self._mandatory
        except AttributeError:
            self._mandatory = False
            return False

    def setMandatory(self, value):
        self._mandatory = value

    def getRegistrationForm(self):
        try:
            if self._regForm:
                pass
        except AttributeError, e:
            self._regForm = None
        return self._regForm

    def getConference(self):
        if self.getRegistrationForm() is not None:
            return self.getRegistrationForm().getConference()
        return None

    def _getDefaultIntroValue(self):
        return "Select the social events you would like to attend and how many places you will need"

    def getIntroSentence(self):
        try:
            if self._introSentence:
                pass
        except AttributeError, e:
            self._introSentence = self._getDefaultIntroValue()
        return self._introSentence

    def setIntroSentence(self, intro):
        self._introSentence = intro

    def getSelectionTypeList(self):
        try:
            if self._selectionTypeList:
                pass
        except AttributeError, e:
            self._selectionTypeList = {"multiple": "Multiple choice",
                                     "unique": "Unique choice"}
        return self._selectionTypeList

    def _getSelectionType(self):
        try:
            if self._selectionType:
                pass
        except AttributeError, e:
            self._selectionType = "multiple"
        return self._selectionType

    def getSelectionTypeId(self):
        return self._getSelectionType()

    def getSelectionTypeCaption(self):
        return self.getSelectionTypeList()[self._getSelectionType()]

    def setSelectionType(self, id):
        self._selectionType = id

    def _generateNewSocialEventItemId(self):
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
        v = self._socialEvents.values()
        if sort:
            v.sort(SocialEventItem._cmpCaption)
        return v

    def clearSocialEventList(self):
        for se in self.getSocialEventList():
            self.removeSocialEvent(se)

    def getLocator(self):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the GeneralField instance """
        if self.getConference() == None:
            return Locator()
        lconf = self.getConference().getLocator()
        lconf["sectionFieldId"] = self.getId()
        return lconf


class StatusValue(Persistent):

    def __init__(self, st, data=None):
        self._status = st
        self._id = ""
        self._caption = ""
        if data is not None:
            self.setValues(data)

    def getValues(self):
        d = {}
        d["caption"] = self.getCaption()
        return d

    def setValues(self, d):
        self.setCaption(d.get("caption", "-- no caption --"))

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getCaption(self):
        return self._caption

    def setCaption(self, cp):
        self._caption = cp

    def clone(self, st):
        sv = StatusValue(st)
        sv.setCaption(self.getCaption())
        return sv

    def _cmpCaption(sv1, sv2):
        return cmp(sv1.getCaption().strip().lower(), sv2.getCaption().strip().lower())
    _cmpCaption = staticmethod(_cmpCaption)


class Status(Persistent):

    def __init__(self, regForm, data=None):
        self._regForm = regForm
        self._statusValues = {}
        self._valuesGenerator = Counter()
        self._id = ""
        self._caption = ""
        self._defaultValue = None
        if data is not None:
            self.setValues(data)
        self.addStatusValue(StatusValue(self, {"caption":"Yes"}))
        self.addStatusValue(StatusValue(self, {"caption":"No"}))

    def setValues(self, d):
        self.setCaption(d.get("caption", ""))
        ids = []
        defaultValueSet = False
        if d.has_key("values") and type(d.get("values", [])) == list:
            for vd in d.get("values", []):
                id = vd.get("id", "")
                if self.getStatusValueById(id) is not None:
                    v = self.getStatusValueById(id)
                    v.setValues(vd)
                else:
                    v = StatusValue(self, vd)
                    self.addStatusValue(v)
                if d.get("defaultvalue", "").strip() == id:
                    defaultValueSet = True
                    self.setDefaultValue(v)
                ids.append(v.getId())
        if not defaultValueSet:
            self.setDefaultValue(None)
        for v in self.getStatusValuesList()[:]:
            if v.getId() not in ids:
                self.removeStatusValue(v)

    def getValues(self):
        d = {}
        d["caption"] = self.getCaption()
        return d

    def getConference(self):
        return self._regForm.getConference()

    def getId(self):
        return self._id

    def setId(self, i):
        self._id = i

    def getCaption(self):
        return self._caption

    def setCaption(self, c):
        self._caption = c

    def setDefaultValue(self, stval):
        self._defaultValue = stval

    def getDefaultValue(self):
        return self._defaultValue

    def _generateValueId(self):
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
        r = self._statusValues.values()
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
        self.getStatusValues()[v.getId()] = v
        self.notifyModification()

    def removeStatusValue(self, v):
        if self.getStatusValues().has_key(v.getId()):
            del self.getStatusValues()[v.getId()]
            self.notifyModification()

    def _cmpCaption(s1, s2):
        return cmp(s1.getCaption().lower().strip(), s2.getCaption().lower().strip())
    _cmpCaption = staticmethod(_cmpCaption)

    def getLocator(self):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the Status instance """
        if self.getConference() == None:
            return Locator()
        lconf = self.getConference().getLocator()
        lconf["statusId"] = self.getId()
        return lconf

    def notifyModification(self):
        """Method called to notify that the registration form has been modified.
        """
        self._p_changed = 1


# Users --------- FINAL INFORMATION STORED FROM THE REGISTRATION FORM

class Registrant(Persistent, Fossilizable):

    fossilizes(IRegFormRegistrantFossil, IRegFormRegistrantBasicFossil, IRegFormRegistrantFullFossil)

    def __init__(self):
        self._conf = None
        self._avatar = None
        self._id = ""
        self._complete = False
        self._registrationDate = nowutc()
        self._checkedIn = False
        self._checkInDate = None
        self._checkInUUID = str(uuid4())

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
        self._accommodation = Accommodation(self)
        self._reasonParticipation = ""

        self._miscellaneous = {}
        self._parmasReturn = {}
        self._statuses = {}
        self._total = 0
        self._hasPay = False
        self._transactionInfo = None

        self._randomId = self._generateRandomId()
        self._attachmentsCounter = Counter()

    def __cmp__(self, other):
        if type(self) is not type(other):
            # This is actually dangerous and the ZODB manual says not to do this
            # because it relies on memory order. However, this branch should never
            # be taken anyway since we do not store different types in the same set
            # or use them as keys.
            return cmp(hash(self), hash(other))
        if self.getConference() == other.getConference():
            return cmp(self.getId(), other.getId())
        return cmp(self.getConference(), other.getConference())

    def isPayedText(self):
        if self.getPayed():
            return "Yes"
        elif not self.doPay():
            return "-"
        return "No"

    def getIdPay(self):
        return "c%sr%s" % (self._conf.getId(), self.getId())

    def setTotal(self, total):
        self._total = total

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
                mg = self.getMiscellaneousGroupById(gs.getId())
                if mg != None:
                    for miscItem in mg.getResponseItemList():
                        if miscItem.isBillable():
                            price = float(miscItem.getPrice() or 0)
                        else:
                            price = 0
                        quantity = miscItem.getQuantity()
                        total += price * quantity
        for bf in self.getBilledForms():
            for item in bf.getBilledItems():
                total += item.getPrice() * item.getQuantity()
        self.setTotal(total)

    def doPay(self):
        return self.getTotal() > 0 and not self.getPayed()

    def setPersonalData(self, data):

        self.getConference().updateRegistrantIndexByEmail(self, data.get("email", ""))

        self.setTitle(data.get("title", ""))
        self.setFirstName(data.get("firstName", ""))
        self.setSurName(data.get("surname", ""))
        self.setPosition(data.get("position", ""))
        self.setInstitution(data.get("institution", ""))
        self.setAddress(data.get("address", ""))
        self.setCity(data.get("city", ""))
        self.setCountry(data.get("country", ""))
        self.setPhone(data.get("phone", ""))
        self.setFax(data.get("fax", ""))
        self.setEmail(data.get("email", ""))
        self.setPersonalHomepage(data.get("personalHomepage", ""))

    def setValues(self, data, av):
        self._avatar = av

        if self.getRegistrationForm().getReasonParticipationForm().isEnabled():
            self.setReasonParticipation(data.get("reason", ""))

        if self.getRegistrationForm().getSessionsForm().isEnabled():
            sessions = data.get("sessions", [])
            if not isinstance(sessions, list):
                sessions = [sessions]
            if not self.getPayed():
                self.setSessions(sessions)
            else:
                # First keep all sessions which are billable (they are not submitted anymore)
                newSessions = [session for session in self.getSessionList() if session.isBillable()]
                # Then take all chosen sessions which are not billable
                newSessions += [session for session in sessions if not session.isBillable()]
                self.setSessions(newSessions)
        else:
            self.setSessions([])

        self.setSessionBillingEnabled(self.getRegistrationForm().getSessionsForm().getType() != "2priorities")

        if self.getRegistrationForm().getAccommodationForm().isEnabled():
            ad = data.get("arrivalDate", None)
            dd = data.get("departureDate", None)
            if ad == "nodate":
                raise FormValuesError(_("Arrival date cannot be empty."))
            elif dd == "nodate":
                raise FormValuesError(_("Departure date cannot be empty."))
            if ad is not None and dd is not None:
                ad = map(lambda x: int(x), ad.split("-"))
                ad = datetime(ad[2], ad[1], ad[0])
                dd = map(lambda x: int(x), dd.split("-"))
                dd = datetime(dd[2], dd[1], dd[0])
                if ad > dd:
                    raise FormValuesError(_("Arrival date has to be earlier than departure date"))
            # Allow changing of the dates only if the current accomodation is not billable or the user hasn't paid yet
            currentAccoType = self._accommodation.getAccommodationType()
            if not self.getPayed() or currentAccoType is None or not currentAccoType.isBillable():
                self._accommodation.setArrivalDate(ad)
                self._accommodation.setDepartureDate(dd)
            accoType = data.get("accommodationType", None)
            if accoType is not None and accoType.isCancelled():
                accoType = None
            if self.getRegistrationForm().getAccommodationForm().getAccommodationTypesList() != []:
                # Only change the accommodation type if:
                # - the registrant hasn't paid yet OR
                # - neither the current nor the new accommodation is billable
                if not self.getPayed() or \
                    ((currentAccoType is None or not currentAccoType.isBillable()) and \
                     (accoType is None or not accoType.isBillable())):
                    if self.getRegistrationForm().getAccommodationForm().getAccommodationTypesList() != [] and data.get("accommodation_type", None) is None:
                        raise FormValuesError(_("It is mandatory to choose an accommodation in order to register"))
                    self._accommodation.setAccommodationType(accoType)
        else: # AccommodationForm disabled
            self._accommodation.setAccommodationType(None)

        if self.getRegistrationForm().getSocialEventForm().isEnabled():
            for seItem in self.getSocialEvents()[:]:
                # Remove all items which can be added back (i.e. if paid only non-billable ones)
                if not (self.getPayed() and seItem.isBillable()):
                    self.removeSocialEventById(seItem.getId())
            for seItem in data.get("socialEvents", []):
                # Only add item if the registrant hasn't paid yet or the item is not billable
                if seItem and (not self.getPayed() or not seItem.isBillable()):
                    newSE = SocialEvent(seItem, int(data.get("places-%s" % seItem.getId(), "1")))
                    self.addSocialEvent(newSE)
            if self.getRegistrationForm().getSocialEventForm().getMandatory() and not self.getSocialEvents():
                raise FormValuesError(_('You have to select at least one social event'))
        else:
            for seItem in self.getSocialEvents()[:]:
                self.removeSocialEventById(seItem.getId())
        #if not self.getPayed():
        #    self._miscellaneous = {}
        total = 0
        for gs in self.getRegistrationForm().getGeneralSectionFormsList():
            if gs.isEnabled():
                mg = self.getMiscellaneousGroupById(gs.getId())
                if mg == None:
                    mg = MiscellaneousInfoGroup(self, gs)
                    self.addMiscellaneousGroup(mg)
                #Mods to support sorting fields
                #for f in gs.getFields():
                for f in gs.getSortedFields():
                    if not f.isDisabled():
                        f.getInput().setResponseValue(mg.getResponseItemById(f.getId()), data, self, mg)
                for miscItem in mg.getResponseItemList():
                    if miscItem.isBillable():
                        price = float(miscItem.getPrice() or 0)
                    else:
                        price = 0
                    quantity = miscItem.getQuantity()
                    total += price * quantity
        for bf in self.getBilledForms():
            for item in bf.getBilledItems():
                total += item.getPrice() * item.getQuantity()
        if not self.getPayed():
            self.setTotal(total)
        self.setPersonalData(self.getRegistrationForm().getPersonalData().getRegistrantValues(self))
        self._complete = True

    def isComplete(self):
        try:
            if self._complete:
                pass
        except AttributeError, e:
            self._complete = False
        return self._complete

    def isCheckedIn(self):
        try:
            if self._checkedIn:
                pass
        except AttributeError:
            self._checkedIn = False
        return self._checkedIn

    def setCheckedIn(self, checkedIn):
        if checkedIn:
            self._checkInDate = nowutc()
        else:
            self._checkInDate = None
        self._checkedIn = checkedIn

    def getCheckInUUID(self):
        try:
            if self._checkInUUID:
                pass
        except AttributeError:
            self._checkInUUID = str(uuid4())
        return self._checkInUUID

    def getCheckInDate(self):
        try:
            if self._checkInDate:
                pass
        except AttributeError:
            self._checkInDate = None
        return self._checkInDate

    def getAdjustedCheckInDate(self,tz=None):
        if not tz:
            tz = self.getConference().getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        checkInDate = self.getCheckInDate()
        if checkInDate:
            return checkInDate.astimezone(timezone(tz))

    def getPayed(self):
        try:
            return self._hasPay
        except:
            self.setPayed(False)
        return self._hasPay

    def setPayed(self, hasPay):
        self._hasPay = hasPay

    def getTransactionInfo(self):
        try:
            return self._transactionInfo
        except:
            self.setTransactionInfo(False)
        return self._transactionInfo

    def setTransactionInfo(self, transactionInfo):
        self._transactionInfo = transactionInfo

    def _generateRandomId(self):
        n = datetime.now()
        return md5(str(random.random() + time.mktime(n.timetuple()))).hexdigest()

    def getRandomId(self):
        try:
            if self._randomId:
                pass
        except AttributeError, e:
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
        if isinstance(self._avatar, MaKaC.user.Avatar):
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

    def getAdjustedRegistrationDate(self, tz=None):
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

    def getFullName(self, title=True, firstNameFirst=False):
        if firstNameFirst:
            res = "%s %s" % (self.getFirstName(), self.getFamilyName())
            res = res.strip()
        else:
            res = safe_upper(self.getFamilyName())
            if self.getFirstName():
                res = "%s, %s" % (res, self.getFirstName())
        if title and self.getTitle():
            res = "%s %s" % (self.getTitle(), res)
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
        for ses in self._sessions:
            ses.setRegistrant(self)
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
        se.setRegistrant(self)
        self.getSocialEvents().append(se)
        self.notifyModification()

    def removeSocialEventById(self, id):
        se = self.getSocialEventById(id)
        se.delete()
        self.getSocialEvents().remove(se)
        self.notifyModification()

    def getLocator(self):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the registrant instance """
        if self.getConference() == None:
            return Locator()
        lconf = self.getConference().getLocator()
        lconf["registrantId"] = self.getId()
        return lconf

    def notifyModification(self):
        """Method called to notify the current registered participant has been modified.
        """
        self._p_changed = 1

    def _cmpFamilyName(r1, r2):
        if r1 is None and r2 is None:
            return 0
        if r1 is None:
            return -1
        if r2 is None:
            return 1
        return cmp(r1.getFamilyName().lower(), r2.getFamilyName().lower())
    _cmpFamilyName = staticmethod(_cmpFamilyName)

    def getMiscellaneousGroups(self):
        try:
            if self._miscellaneous:
                pass
        except AttributeError, e:
            self._miscellaneous = {}
        return self._miscellaneous

    def getMiscellaneousGroupList(self):
        return self.getMiscellaneousGroups().values()

    def getMiscellaneousGroupById(self, id):
        if self.getMiscellaneousGroups().has_key(id):
            return self.getMiscellaneousGroups()[id]
        return None

    def addMiscellaneousGroup(self, g):
        if not self.getMiscellaneousGroups().has_key(g.getId()):
            self.getMiscellaneousGroups()[g.getId()] = g
            self.notifyModification()

    def setSessionBillingEnabled(self, v):
        self._sessionBillingEnabled = v

    def isSessionBillingEnabled(self):
        try:
            return self._sessionBillingEnabled
        except:
            self.setSessionBillingEnabled(False)
        return self._sessionBillingEnabled

    def getBilledForms(self):
        """

        """
        forms = []
        if self._accommodation:
            forms.append(BilledItemsWrapper([self._accommodation]))
        if self._socialEvents:
            forms.append(BilledItemsWrapper(self._socialEvents))
        if self._sessions and self.isSessionBillingEnabled():
            forms.append(BilledItemsWrapper(self._sessions))
        return forms

    def getStatuses(self):
        try:
            if self._statuses:
                pass
        except AttributeError, e:
            self._statuses = {}
        return self._statuses

    def getStatusesList(self):
        return self.getStatuses().values()

    def addStatus(self, s):
        self.getStatuses()[s.getId()] = s
        self.notifyModification()

    def removeStatus(self, s):
        if self.getStatuses().has_key(s.getId()):
            del self.getStatuses()[s.getId()]
            self.notifyModification()

    def getStatusById(self, id):
        v = self.getStatuses().get(id, None)
        if v is None:
            st = self._conf.getRegistrationForm().getStatusById(id)
            v = RegistrantStatus(self, st)
            if st.getDefaultValue() is not None:
                v.setStatusValue(st.getDefaultValue())
            self.addStatus(v)
        return v

    def setModificationDate(self):
        pass

    def getAttachments(self):
        try:
            if self._attachments:
                pass
        except AttributeError:
            self._attachments = {}
        return self._attachments

    def getAttachmentList(self):
        return self.getAttachments().values()

    def getAttachmentById(self, id):
        return self.getAttachments().get(id, None)

    def _getAttachmentsCounter(self):
        try:
            if self._attachmentsCounter:
                pass
        except AttributeError:
            self._attachmentsCounter = Counter()
        return self._attachmentsCounter.newCount()

    def __addFile(self, file):
        file.archive(self.getConference()._getRepository())
        self.getAttachments()[file.getId()] = file
        self.notifyModification()

    def saveFile(self, fileUploaded):
        from MaKaC.conference import LocalFile
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp(suffix="IndicoRegistrant.tmp", dir=tempPath)[1]
        f = open(tempFileName, "wb")
        f.write(fileUploaded.file.read())
        f.close()
        file = LocalFile()
        file.setFileName(fileUploaded.filename)
        file.setFilePath(tempFileName)
        file.setOwner(self)
        file.setId(self._getAttachmentsCounter())
        self.__addFile(file)
        return file

    def deleteFile(self, fileId):
        file = self.getAttachments()[fileId]
        file.delete()
        del self.getAttachments()[fileId]
        self.notifyModification()

    def removeResource(self, res):
        """Necessary because LocalFile.delete (see _deleteFile) is calling this method.
        In our case, nothing to do.
        """
        pass

    def canUserModify(self, user):
        return self.getConference().canUserModify(user) or (user is not None and user == self.getAvatar())


class BilledItemsWrapper(object):

    def __init__(self, items):
        self._items = items

    def getBilledItems(self):
        return [item.getBilledItem() for item in self._items if item.isBillable() and not item.isCancelled()]


class BilledItem(object):

    def __init__(self, caption, price, quantity, currency):
        self._caption = caption
        self._price = price
        self._quantity = quantity
        self._currency = currency

    def getCaption(self):
        return self._caption

    def getPrice(self):
        return float(self._price)

    def getQuantity(self):
        return self._quantity

    def getCurrency(self):
        return self._currency


class Accommodation(Persistent):

    def __init__(self, reg=None):
        self._registrant = reg
        self._arrivalDate = None
        self._departureDate = None
        self._accommodationType = None
        self._price = 0
        self._billable = False
        self._currency = ""

    def isCancelled(self):
        return self._accommodationType.isCancelled()

    def getRegistrant(self):
        try:
            return self._registrant
        except:
            return None

    def setRegistrant(self, reg):
        self._registrant = reg

    def getArrivalDate(self):
        return self._arrivalDate

    def setArrivalDate(self, ad):
        self._arrivalDate = ad

    def getDepartureDate(self):
        return self._departureDate

    def setDepartureDate(self, dd):
        self._departureDate = dd

    def getNights(self):
        return (self._departureDate - self._arrivalDate).days

    def getPrice(self):
        try:
            return self._price
        except:
            return 0

    def isBillable(self):
        try:
            return self._billable
        except:
            return False

    def getCurrency(self):
        try:
            return self._currency
        except:
            self._currency = self._regForm.getCurrency()
        return self._currency

    def getBilledItem(self):
        return BilledItem(self._accommodationType.getCaption(), self.getPrice(), self.getNights(), self.getCurrency())

    def getAccommodationType(self):
        return self._accommodationType

    def setAccommodationType(self, at):
        if self.getAccommodationType() != at:
            if self.getAccommodationType() is not None:
                self.getAccommodationType().decreaseNoPlaces()
            if at is not None:
                at.increaseNoPlaces()
                self._price = at.getPrice()
                self._billable = at.isBillable()
                self._currency = at.getCurrency()
            else:
                self._price = 0
                self._billable = False
                self._currency = ""
            self._accommodationType = at


class SocialEvent(Persistent, Fossilizable):

    fossilizes(IRegFormSocialEventFossil)

    def __init__(self, se, noPlaces, reg=None):
        self._registrant = None
        self.addSEItem(se, noPlaces)

    def addSEItem(self, se, noPlaces):
        self._socialEventItem = se
        self._noPlaces = noPlaces
        self._socialEventItem.increaseNoPlaces(noPlaces)
        self._price = self._socialEventItem.getPrice()
        self._pricePerPlace = self._socialEventItem.isPricePerPlace()
        self._billable = self._socialEventItem.isBillable()
        self._currency = self._socialEventItem.getCurrency()

    def getRegistrant(self):
        try:
            return self._registrant
        except:
            return None

    def setRegistrant(self, reg):
        self._registrant = reg

    def getNoPlaces(self):
        return self._noPlaces

    def getCurrency(self):
        try:
            return self._currency
        except:
            self._currency = self._socialEventItem.getCurrency()
        return self._currency

    def getPrice(self):
        try:
            return self._price
        except:
            return 0

    def isBillable(self):
        try:
            return self._billable
        except:
            return False

    def isPricePerPlace(self):
        try:
            return self._pricePerPlace
        except:
            return False

    def getBilledItem(self):
        quantity = 1
        if self._pricePerPlace:
            quantity = self.getNoPlaces()
        return BilledItem(self.getCaption(), self.getPrice(), quantity, self.getCurrency())

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


class RegistrantSession(Persistent):

    def __init__(self, ses, reg=None):
        self._regSession = ses
        self._registrant = reg
        self._price = self._regSession.getPrice()
        self._billable = self._regSession.isBillable()
        self._currency = self._regSession.getCurrency()

    def getRegistrant(self):
        return self._registrant

    def setRegistrant(self, reg):
        self._registrant = reg

    def getCurrency(self):
        if not hasattr(self, "_currency") or not self._currency:
            self._currency = self._regSession.getCurrency()
        return self._currency

    def getPrice(self):
        try:
            return self._price
        except:
            return 0

    def isBillable(self):
        try:
            return self._billable
        except:
            return False

    def getBilledItem(self):
        return BilledItem(self.getCaption(), self.getPrice(), 1, self.getCurrency())

    def getRegSession(self):
        return self._regSession

    def getSession(self):
        return self._regSession.getSession()

    def getId(self):
        return self._regSession.getId()

    def getCaption(self):
        return self._regSession.getCaption()
    getTitle = getCaption

    def getCode(self):
        return self._regSession.getCode()

    def isCancelled(self):
        return self._regSession.isCancelled()


class MiscellaneousInfoGroup(Persistent, Fossilizable):

    fossilizes(IRegFormMiscellaneousInfoGroupFossil)

    def __init__(self, reg, gs):
        self._registrant = reg
        self._generalSection = gs
        self._id = gs.getId()
        self._responseItems = {}

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
        self._responseItems[r.getId()] = r
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
            self._responseItems = {}
            self.notifyModification()
        else:
            #Mods to support sorting fields
            #for f in gs.getFields():
            for f in gs.getSortedFields():
                self.removeResponseItem(f)

    def getLocator(self):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the MiscellaneousInfoGroup instance """
        lconf = self.getRegistrant().getLocator()
        lconf["miscInfoId"] = self.getId()
        return lconf

    def notifyModification(self):
        self._p_changed = 1


class MiscellaneousInfoSimpleItem(Persistent):

    def __init__(self, group, field):
        self._group = group
        self._generalField = field
        self._id = field.getId()
        self._value = None
        self._billable = False
        self._price = 0.0
        self._quantity = 0
        self._currency = ""
        self._mandatory = False
        # TODO: When migrate to new database, take into account that HTMLName cannot be empty string
        self._HTMLName = ""

    def getHTMLName(self):
        try:
            if self._HTMLName == "":
                self._HTMLName = self.getGeneralField().getInput().getHTMLName()
        except:
            self._HTMLName = ""
        return self._HTMLName

    def setHTMLName(self, HTMLName):
        self._HTMLName = HTMLName

    def isMandatory(self):
        try:
            return self._mandatory
        except:
            self._mandatory = False
        return self._mandatory

    def setMandatory(self, mandatory):
        self._mandatory = mandatory

    def getCurrency(self):
        try:
            return self._currency
        except:
            self.setCurrency("")
        return self._currency

    def setCurrency(self, currency):
        self._currency = currency

    def getQuantity(self):
        try:
            return self._quantity
        except:
            self.setQuantity(0)
        return self._quantity

    def setQuantity(self, quantity):
        self._quantity = quantity

    def isBillable(self):
        try:
            return self._billable
        except:
            self.setBillable(False)
        return self._billable

    def setBillable(self, v):
        self._billable = v

    def getPrice(self):
        try:
            return self._price
        except:
            self.setPrice(0)
        return self._price

    def setPrice(self, price):
        self._price = price

    def getId(self):
        return self._id

    def getGeneralField(self):
        return self._generalField

    def getCaption(self):
        return self._generalField.getCaption()

    def getOwner(self):
        return self._group
    getGroup = getOwner

    def getValue(self):
        return self._value

    def setValue(self, v):
        self._value = v


class RegistrantStatus(Persistent):

    def __init__(self, reg, st, data=None):
        self._status = st
        self._registrant = reg
        self._value = None
        if data is not None:
            self.setValues()

    def setValues(self, d):
        self.setStatusValue(d.get("statusvalue", ""))

    def getValues(self):
        d = {}
        d["statusvalue"] = self.getStatusValue()
        return d

    def getId(self):
        return self._status.getId()

    def getCaption(self):
        return self._status.getCaption()

    def getStatusValue(self):
        if not self._status.hasStatusValue(self._value):
            self._value = self._status.getDefaultValue()
        return self._value

    def setStatusValue(self, v):
        self._value = v


class RegistrantMapping(object):

    def __init__(self, registrant):
        self._registrant = registrant
        self._regDict = {
                        "FirstName":           self._registrant.getFirstName,
                        "LastName":            self._registrant.getSurName,
                        "Institution":         self._registrant.getInstitution,
                        "Position":            self._registrant.getPosition,
                        "Phone":               self._registrant.getPhone,
                        "City":                self._registrant.getCity,
                        "Address":             self._registrant.getAddress,
                        "Email":               self._registrant.getEmail,
                        "isPayed":             self._registrant.isPayedText,
                        "idpayment":           self._registrant.getIdPay,
                        "Country":             self._getCountry,
                        "amountToPay":         self._getAmountToPay,
                        "Accommodation":       self._getAccomodation,
                        "SocialEvents":        self._getSocialEvents,
                        "ReasonParticipation": self._getReasonParticipation,
                        "RegistrationDate":    self._getRegistrationDate,
                        "Sessions":            self._getSessions,
                        "DepartureDate":       self._getDepartureDate,
                        "ArrivalDate":         self._getArrivalDate,
                        "checkedIn":           self._getCheckedIn,
                        "checkInDate":         self._getCheckInDate
                        }

    def __getitem__(self, key):
        if self._regDict.has_key(key):
            return self._regDict[key]()
        elif re.match("s-[0-9]+$", key):
            return self._getStatus(key[2:])
        elif re.match("[0-9]+$", key):
            return self._getGroup(key)
        elif re.match("[0-9]+-[0-9]+$", key):
            dashPos = key.find('-')
            return self._getItem(key[:dashPos], key[dashPos + 1:])
        else:
            return "&nbsp;"

    def _getCountry(self):
        return CountryHolder().getCountryById(self._registrant.getCountry())

    def _getAmountToPay(self):
        return "%.2f %s" % (self._registrant.getTotal(), self._registrant.getConference().getRegistrationForm().getCurrency())

    def _getAccomodation(self):
        if self._registrant.getAccommodation() is not None:
            if self._registrant.getAccommodation().getAccommodationType() is not None:
                return self._registrant.getAccommodation().getAccommodationType().getCaption()
        return ""

    def _getDepartureDate(self):
        accomodation = self._registrant.getAccommodation()
        if accomodation is not None:
            departure_date = accomodation.getDepartureDate()
            if departure_date is not None:
                return format_date(departure_date)
        return ""

    def _getArrivalDate(self):
        accomodation = self._registrant.getAccommodation()
        if accomodation is not None:
            arrival_date = accomodation.getArrivalDate()
            if arrival_date is not None:
                return format_date(arrival_date)
        return ""

    def _getSocialEvents(self):
        events = self._registrant.getSocialEvents()
        items = ["%s (%s)" % (item.getCaption(), item.getNoPlaces()) for item in events ]
        return "<br>".join(items)

    def _getReasonParticipation(self):
        return self._registrant.getReasonParticipation() or ""

    def _getRegistrationDate(self):
        registration_date = self._registrant.getAdjustedRegistrationDate()
        if registration_date is not None:
            return format_datetime(registration_date)
        else:
            return i18nformat("""--  _("date unknown")--""")

    def _getSessions(self):
        sessions = self._registrant.getSessionList()
        return "<br>".join([sess.getTitle() for sess in sessions])

    def _getStatus(self, id):
        st = self._registrant.getStatusById(id)
        if st.getStatusValue() is not None:
            return st.getStatusValue().getCaption()
        else:
            return i18nformat("""<span style="white-space:nowrap">--  _("not set") --</span>""")

    def _getGroup(self, groupId):
        if self._registrant.getMiscellaneousGroupById(groupId):
            return self._registrant.getMiscellaneousGroupById(groupId).getTitle()
        else:
            return ""

    def _formatValue(self, fieldInput, value):
        try:
            value = fieldInput.getValueDisplay(value)
        except:
            value = str(value).strip()
        return value

    def _getItem(self, groupId, itemId):
        if self._registrant.getMiscellaneousGroupById(groupId) and \
           self._registrant.getMiscellaneousGroupById(groupId).getResponseItemById(itemId):
            item = self._registrant.getMiscellaneousGroupById(groupId).getResponseItemById(itemId)
            return self._formatValue(item.getGeneralField().getInput(), item.getValue())
        else:
            return ""

    def _getCheckedIn(self):
        conf = self._registrant.getConference()
        if not conf.getRegistrationForm().getETicket().isEnabled():
            return "-"
        elif self._registrant.isCheckedIn():
            return _("Yes")
        else:
            return _("No")

    def _getCheckInDate(self):
        checkInDate = self._registrant.getAdjustedCheckInDate()
        if checkInDate:
            return format_datetime(checkInDate)
        else:
            return "-"
