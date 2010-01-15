# -*- coding: utf-8 -*-
##
## $Id: excel.py,v 1.11 2009/05/14 18:05:54 jose Exp $
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

from MaKaC.webinterface.common.countries import CountryHolder
from MaKaC.common import utils

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

    def addValue(self, value):
        """Add a new cell value to the current line"""
        self._currentLine.append(ExcelGenerator.excelFormatting(value))

    def addNumberAsString(self, value):
        """Add a new cell value (which it has to be interpreted like 
        a string not like a number) to the current line"""
        if value.strip()!="":
            self._currentLine.append("=%s"%ExcelGenerator.excelFormatting(value).replace(",",";"))
            
        else:
            self._currentLine.append("")

    def newLine(self):
        """Creates a new line for the excel file"""
        self._lines.append(";".join(self._currentLine))
        self._currentLine=[]

    def getExcelContent(self):
        if self._currentLine!=[]:
            self.newLine()
        return "\r\n".join(self._lines)

    def excelFormatting(text):
        if text.strip()!="":
            text=utils.utf8Tolatin1(text)
            text=text.replace('"','""')
            text="\"%s\""%text
        return text
    excelFormatting=staticmethod(excelFormatting)
        



class RegistrantsListToExcel:
    
    def __init__(self, conf,list=None, display=["Institution", "Phone", "City", "Country"]):
        self._conf = conf
        self._regForm = conf.getRegistrationForm()
        self._regList = list
        self._display = display
        
    def getExcelFile(self):
        excelGen=ExcelGenerator()
        excelGen.addValue("Name")
        for key in self._display:
            if key in ["Email", "Position", "Institution", "Phone", "City", "Country", "Address"]:
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
                if key == "Email":
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
                    excelGen.addValue(reg.getPhone())
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
                                excelGen.addValue(str(i.getValue()))
                                continue
                    excelGen.addValue("")
            excelGen.newLine()
        return excelGen.getExcelContent()

        
class AbstractListToExcel:
    
    def __init__(self, conf,list=None, display=["ID","Title","Primary Authors","Track Name","Contribution Type"]):
        self._conf = conf        
        self._abstractList = list
        self._displayList = display
        
    def getExcelFile(self):
        excelGen=ExcelGenerator()        
        for key in self._displayList:            
            excelGen.addValue(key)
            
        excelGen.newLine()

        if self._abstractList is None:
            self._abstractList = self._conf.getAbstractMgr().getAbstractList()
            
        for abstract in self._abstractList :            
            for key in self._displayList :
                if key == "ID" :
                    excelGen.addValue(abstract.getId())
                elif key == "Title" :
                    excelGen.addValue(abstract.getTitle())
                elif key == "Primary Authors" :
                    paList = []
                    for pa in abstract.getPrimaryAuthorList() :
                        paList.append(pa.getFullName())
                    excelGen.addValue("; ".join(paList))
                elif key == "Track Name":
                    trList = []
                    for tr in abstract.getTrackList() :
                        trList.append(tr.getTitle())
                    excelGen.addValue("; ".join(trList))
                elif key == "Contribution Type":
                    contribType=abstract.getContribType()
                    ctname=""
                    if contribType is not None:
                        ctname=contribType.getName()
                    excelGen.addNumberAsString(ctname)                
            excelGen.newLine()
        return excelGen.getExcelContent()

class ParticipantsListToExcel:
    
    def __init__(self, conf,list=None):
        self._conf = conf
        self._partList = list
        
    def getExcelFile(self):
        excelGen=ExcelGenerator()
        excelGen.addValue("Name")
        excelGen.addValue("Email")
        excelGen.addValue("Affiliation")
        excelGen.addValue("Phone")
        excelGen.addValue("Fax")
        excelGen.newLine()

        if self._partList == None:
            self._partList = self._conf.getParticipation().getParticipantList()
            
        for reg in self._partList:
            excelGen.addValue(reg.getFullName())
            excelGen.addValue(reg.getEmail())
            excelGen.addValue(reg.getAffiliation())
            excelGen.addNumberAsString(reg.getTelephone())
            excelGen.addNumberAsString(reg.getFax())
            excelGen.newLine()
        return excelGen.getExcelContent()
