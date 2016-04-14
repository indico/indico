# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from datetime import datetime
from MaKaC.review import AbstractStatusAccepted, AbstractStatusProposedToAccept
from MaKaC.webinterface.common.abstractStatusWrapper import AbstractStatusList
from indico.util.date_time import format_date
import csv
import codecs


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
                        ctname = contribType.name
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

            resource_list = []

            for attachment in contrib.attached_items.get('files', []):
                resource_list.append(attachment.absolute_download_url)

            for folder in contrib.attached_items.get('folders', []):
                for attachment in folder.attachments:
                    resource_list.append(attachment.absolute_download_url)

            excelGen.addValue("\n".join(resource_list))
            excelGen.newLine()

        return excelGen.getExcelContent()
