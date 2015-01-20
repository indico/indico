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

from MaKaC.webinterface.common.countries import CountryHolder
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from MaKaC.common import utils
from datetime import datetime
from MaKaC.conference import Link
from MaKaC.webinterface import urlHandlers
from MaKaC.conference import LocalFile
from MaKaC.review import AbstractStatusAccepted, AbstractStatusProposedToAccept
from MaKaC.webinterface.common.abstractStatusWrapper import AbstractStatusList
from indico.util.date_time import format_date
import csv, codecs

class ExcelGenerator:
    """It helps to create an Excel CSV file. The way to work with this class
    is the following:
        - Use always "addValue" for adding all the cell values to the current
        line, including empty strings.
        - Once the line was completely filled use "newLine" to follow with the
        filling of the next line of the CSV file.
    For instance:
        excelGen=ExcelGenerator()
        for n in range(0,5):
            for i in ["a","b","c","d"]:
                excelGen.addValue("%s-%s"%(n,i))
            excelGen.newLine()
        print excelGen.getExcelContent()

        The CSV output file will be:
        "0-a";"0-b";"0-c";"0-d"
        "1-a";"1-b";"1-c";"1-d"
        "2-a";"2-b";"2-c";"2-d"
        "3-a";"3-b";"3-c";"3-d"
        "4-a";"4-b";"4-c";"4-d"
        """

    def __init__(self):
        self._lines=[]
        self._currentLine=[]
        self._writer = csv.writer(self, quoting=csv.QUOTE_NONNUMERIC)

    def addValue(self, value):
        """Add a new cell value to the current line"""
        value = ExcelGenerator.excelFormatting(value)
        self._currentLine.append(value)

    def write(self, value):
        self._lines.append(value)

    def addNumberAsString(self, value, excelSpecific=True):
        """Add a new cell value (which it has to be interpreted like
        a string not like a number) to the current line. Needed just for Excel (not for OpenOffice)."""
        if excelSpecific and value.strip() != "":
            value = '="%s"' % ExcelGenerator.excelFormatting(value)
        self._currentLine.append(value)

    def newLine(self):
        """Creates a new line for the excel file"""
        self._writer.writerow(self._currentLine)
        self._currentLine = []

    def getExcelContent(self):
        if self._currentLine != []:
            self.newLine()
        return codecs.BOM_UTF8 + ''.join(self._lines)

    def excelFormatting(text):
        if text is None:
            text = ""
        if text.strip() != "":
            text = text.replace('\x0d', '')
        return text
    excelFormatting=staticmethod(excelFormatting)

class RegistrantsListToExcel:

    def __init__(self, conf,list=None, display=["Institution", "Phone", "City", "Country"], excelSpecific=True):
        self._conf = conf
        self._regForm = conf.getRegistrationForm()
        self._regList = list
        self._display = display
        self._excelSpecific = excelSpecific

    def _formatGenericValue(self, fieldInput, value):
        try:
            if not isinstance(value, LocalFile):
                value = fieldInput.getValueDisplay(value)
            else: # if file, use just the filename, not the html link returned by getValueDisplay
                value = str(value).strip()
        except:
            value = str(value).strip()
        return value

    def _isNumberAsString(self, fieldInput, value):
        return fieldInput.getName() == 'Telephone'

    def getExcelFile(self):
        excelGen=ExcelGenerator()
        excelGen.addValue("Name")
        for key in self._display:
            if key in ["Id", "Email", "Position", "Institution", "Phone", "City", "Country", "Address"]:
                excelGen.addValue(key)
            elif key=="Accommodation":
                excelGen.addValue(self._regForm.getAccommodationForm().getTitle())
            elif key == "SocialEvents":
                excelGen.addValue(self._regForm.getSocialEventForm().getTitle())
            elif key == "Sessions":
                excelGen.addValue(self._regForm.getSessionsForm().getTitle())
            elif key=="ArrivalDate":
                excelGen.addValue("Arrival Date")
            elif key=="DepartureDate":
                excelGen.addValue("Departure Date")
            elif key=="RegistrationDate":
                excelGen.addValue("Registration Date")
            elif key == "ReasonParticipation":
                excelGen.addValue(self._regForm.getReasonParticipationForm().getTitle())
            elif key == "isPayed":
                excelGen.addValue("Paid")
            elif key == "idpayment":
                excelGen.addValue("Payment ID")
            elif key == "amountToPay":
                excelGen.addValue("Amount")
            elif key == "FirstName":
                excelGen.addValue("First name")
            elif key == "LastName":
                excelGen.addValue("Last name")
            elif key.startswith("s-"):
                ids=key.split("-")
                if len(ids)==2:
                    status=self._regForm.getStatusById(ids[1])
                    excelGen.addValue(status.getCaption())
                else:
                    excelGen.addValue("")
            else:
                ids=key.split("-")
                if len(ids)==2:
                    group=self._regForm.getSectionById(ids[0])
                    if group is not None:
                        i=group.getFieldById(ids[1])
                        if i is not None:
                            excelGen.addValue(i.getCaption())
                            continue
                excelGen.addValue("")
        excelGen.newLine()

        if self._regList == None:
            self._regList = self._conf.getRegistrantsList(True)

        for reg in self._regList:
            excelGen.addValue(reg.getFullName())
            for key in self._display:
                if key == "Id":
                    excelGen.addValue(reg.getId())
                elif key == "Email":
                    excelGen.addValue(reg.getEmail())
                elif key == "Institution":
                    excelGen.addValue(reg.getInstitution())
                elif key == "Position":
                    excelGen.addValue(reg.getPosition())
                elif key == "City":
                    excelGen.addValue(reg.getCity())
                elif key == "Country":
                    excelGen.addValue(CountryHolder().getCountryById(reg.getCountry()))
                elif key == "Address":
                    excelGen.addValue(reg.getAddress())
                elif key == "Phone":
                    excelGen.addNumberAsString(reg.getPhone(), self._excelSpecific)
                elif key == "Sessions":
                    p7 = []
                    for ses in reg.getSessionList():
                        if ses is not None:
                            p7.append(ses.getTitle().strip() or "")
                    excelGen.addValue("; ".join(p7))
                elif key == "SocialEvents":
                    p8 = []
                    for se in reg.getSocialEvents():
                        if se is not None:
                            p8.append("%s (%s)"%(se.getCaption().strip(), se.getNoPlaces()) or "")
                    excelGen.addValue("; ".join(p8))
                elif key == "Accommodation":
                    if reg.getAccommodation() is not None and reg.getAccommodation().getAccommodationType() is not None:
                        excelGen.addValue(reg.getAccommodation().getAccommodationType().getCaption())
                    else:
                        excelGen.addValue("")
                elif key == "ArrivalDate":
                    if reg.getAccommodation() is not None and reg.getAccommodation().getArrivalDate() is not None:
                        excelGen.addValue(reg.getAccommodation().getArrivalDate().strftime("%d-%B-%Y"))
                    else:
                        excelGen.addValue("")
                elif key == "DepartureDate":
                    if reg.getAccommodation() is not None and reg.getAccommodation().getDepartureDate() is not None:
                        excelGen.addValue(reg.getAccommodation().getDepartureDate().strftime("%d-%B-%Y"))
                    else:
                        excelGen.addValue("")
                elif key == "ReasonParticipation":
                    excelGen.addValue(reg.getReasonParticipation())
                elif key == "isPayed":
                    excelGen.addValue(reg.isPayedText())
                elif key == "idpayment":
                    excelGen.addValue(reg.getIdPay())
                elif key == "FirstName":
                    excelGen.addValue(reg.getFirstName())
                elif key == "LastName":
                    excelGen.addValue(reg.getSurName())
                elif key == "amountToPay":
                    excelGen.addValue("%.2f %s"%(reg.getTotal(), reg.getConference().getRegistrationForm().getCurrency()))
                elif key == "RegistrationDate":
                    if reg.getRegistrationDate() is not None:
                        excelGen.addValue(reg.getAdjustedRegistrationDate().strftime("%d-%B-%Y-%H:%M"))
                    else:
                        excelGen.addValue("")
                elif key.startswith("s-"):
                    ids=key.split("-")
                    if len(ids)==2:
                        status=reg.getStatusById(ids[1])
                        cap=""
                        if status.getStatusValue() is not None:
                            cap=status.getStatusValue().getCaption()
                        excelGen.addValue(cap)
                else:
                    ids=key.split("-")
                    if len(ids)==2:
                        group=reg.getMiscellaneousGroupById(ids[0])
                        if group is not None:
                            i=group.getResponseItemById(ids[1])
                            if i is not None:
                                value = self._formatGenericValue(i.getGeneralField().getInput(), i.getValue())
                                if self._isNumberAsString(i.getGeneralField().getInput(), i.getValue()):
                                    excelGen.addNumberAsString(value, self._excelSpecific)
                                else:
                                    excelGen.addValue(value)
                                continue
                    excelGen.addValue("")
            excelGen.newLine()
        return excelGen.getExcelContent()


class AbstractListToExcel:

    def __init__(self, conf, abstractList=None, display=["ID", "Title", "PrimaryAuthor", "Tracks", "Type", "Status", "Rating", "AccTrack", "AccType", "SubmissionDate", "ModificationDate"], excelSpecific=True):
        self._conf = conf
        self._abstractList = abstractList
        self._displayList = display
        self._excelSpecific = excelSpecific

    def getExcelFile(self):
        excelGen = ExcelGenerator()
        for key in self._displayList:
            excelGen.addValue(key)

        excelGen.newLine()

        if self._abstractList is None:
            self._abstractList = self._conf.getAbstractMgr().getAbstractList()

        for abstract in self._abstractList:
            for key in self._displayList:
                status = abstract.getCurrentStatus()
                isStatusAccpeted = isinstance(status, (AbstractStatusAccepted, AbstractStatusProposedToAccept))
                if key == "ID":
                    excelGen.addValue(abstract.getId())
                elif key == "Title":
                    excelGen.addValue(abstract.getTitle())
                elif key == "PrimaryAuthor":
                    paList = []
                    for pa in abstract.getPrimaryAuthorList():
                        paList.append(pa.getFullName())
                    excelGen.addValue("; ".join(paList))
                elif key == "Tracks":
                    trList = []
                    for tr in abstract.getTrackList():
                        trList.append(tr.getTitle())
                    excelGen.addValue("; ".join(trList))
                elif key == "Type":
                    contribType = abstract.getContribType()
                    ctname = ""
                    if contribType is not None:
                        ctname = contribType.getName()
                    excelGen.addValue(ctname)
                elif key == "Status":
                    excelGen.addValue(AbstractStatusList.getInstance().getCaption(status.__class__))
                elif key == "Rating":
                    if abstract.getRating():
                        excelGen.addValue("%.2f" % abstract.getRating())
                    else:
                        excelGen.addNumberAsString("-", self._excelSpecific)
                elif key == "AccTrack":
                    accTrack = ""
                    if isStatusAccpeted and status.getTrack():
                        accTrack = status.getTrack().getCode()
                    excelGen.addValue(accTrack)
                elif key == "AccType":
                    accType = ""
                    if isStatusAccpeted and status.getType():
                        accType = status.getType().getName()
                    excelGen.addValue(accType)
                elif key == "SubmissionDate":
                    excelGen.addValue(format_date(abstract.getSubmissionDate(), format="short"))
                elif key == "ModificationDate":
                    excelGen.addValue(format_date(abstract.getModificationDate(), format="short"))

            excelGen.newLine()
        return excelGen.getExcelContent()

class ParticipantsListToExcel:

    def __init__(self, conf,list=None, excelSpecific=True):
        self._conf = conf
        self._partList = list
        self._excelSpecific = excelSpecific

    def getExcelFile(self):
        excelGen=ExcelGenerator()
        excelGen.addValue("Name")
        excelGen.addValue("Email")
        excelGen.addValue("Affiliation")
        excelGen.addValue("Address")
        excelGen.addNumberAsString("Phone", self._excelSpecific)
        excelGen.addNumberAsString("Fax", self._excelSpecific)
        excelGen.newLine()

        if self._partList == None:
            self._partList = self._conf.getParticipation().getParticipantList()

        for reg in self._partList:
            excelGen.addValue(reg.getFullName())
            excelGen.addValue(reg.getEmail())
            excelGen.addValue(reg.getAffiliation())
            excelGen.addValue(reg.getAddress())
            excelGen.addNumberAsString(reg.getTelephone(), self._excelSpecific)
            excelGen.addNumberAsString(reg.getFax(), self._excelSpecific)
            excelGen.newLine()
        return excelGen.getExcelContent()



class ContributionsListToExcel:

    def __init__(self, conf,contribList=None, tz=None):
        self._conf = conf
        self._contribList = contribList
        if not tz:
            self._tz = self._conf.getTimezone()
        else:
            self._tz = tz

    def getExcelFile(self):
        excelGen=ExcelGenerator()
        excelGen.addValue("Id")
        excelGen.addValue("Date")
        excelGen.addValue("Duration")
        excelGen.addValue("Type")
        excelGen.addValue("Title")
        excelGen.addValue("Presenter")
        excelGen.addValue("Session")
        excelGen.addValue("Track")
        excelGen.addValue("Status")
        excelGen.addValue("Material")
        excelGen.newLine()

        for contrib in self._contribList:
            excelGen.addValue(contrib.getId())
            startDate = contrib.getAdjustedStartDate(self._tz)
            if startDate:
                excelGen.addValue(startDate.strftime("%A %d %b %Y at %H:%M"))
            else:
                excelGen.addValue("")
            excelGen.addValue((datetime(1900,1,1)+contrib.getDuration()).strftime("%Hh%M'"))
            type = contrib.getType()
            if type:
                excelGen.addValue(type.getName())
            else:
                excelGen.addValue("")
            excelGen.addValue(contrib.getTitle())
            listSpeaker = []
            for speaker in contrib.getSpeakerList():
                listSpeaker.append(speaker.getFullName())
            excelGen.addValue("\n".join(listSpeaker))
            session = contrib.getSession()
            if session:
                excelGen.addValue(session.getTitle())
            else:
                excelGen.addValue("")
            track = contrib.getTrack()
            if track:
                excelGen.addValue(track.getTitle())
            else:
                excelGen.addValue("")
            status=contrib.getCurrentStatus()
            excelGen.addValue(ContribStatusList().getCaption(status.__class__))
            listResource = []
            for material in contrib.getAllMaterialList():
                for resource in material.getResourceList():
                    if isinstance(resource, Link):
                        listResource.append(resource.getURL())
                    else:
                        listResource.append(str(urlHandlers.UHFileAccess.getURL( resource )))
            excelGen.addValue("\n".join(listResource))
            excelGen.newLine()

        return excelGen.getExcelContent()
