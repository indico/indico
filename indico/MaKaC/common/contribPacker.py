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

#import sys
#sys.path.append("c:/development/indico/code/code")

import zipfile
import tempfile
import string
import os
from datetime import timedelta, datetime

from indico.util.date_time import format_date

from MaKaC.common.utils import utf8rep
from MaKaC.errors import MaKaCError
from MaKaC import conference
from MaKaC import schedule
from indico.core.config import Config
from MaKaC.PDFinterface.conference import ProceedingsTOC, ProceedingsChapterSeparator
from MaKaC.i18n import _


class ZIPFileHandler:

    def __init__(self):
        (fh, name) = tempfile.mkstemp(prefix="Indico", dir=Config.getInstance().getTempDir())
        os.fdopen(fh).close()
        try:
            self._file = zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED, allowZip64=True)
        except:
            self._file = zipfile.ZipFile(name, "w", allowZip64=True)
        self._name = name

    def _normalisePath(self, path):
        forbiddenChars = string.maketrans(" :()*?<>|\"", "__________")
        path = path.translate(forbiddenChars)
        return path

    def add(self, name, path):
        name = utf8rep(name)
        self._file.write(str(path), self._normalisePath(name))

    def addNewFile(self, name, bytes):
        if not self.hasFile(name):
            name = utf8rep(name)
            self._file.writestr(name, bytes)

    def addDir(self, path):
        normalized_path = os.path.join(self._normalisePath(path), "indico_file.dat")
        if not self.hasFile(normalized_path):
            self.addNewFile(normalized_path, "# Indico File")

    def close(self):
        self._file.close()

    def getPath(self):
        return self._name

    def hasFile(self, fileName):
        for zfile in self._file.infolist():
            if zfile.filename == fileName:
                return True
        return False


class AbstractPacker:
    """
    """

    def __init__(self,conf):
        self._conf=conf

    def _normalisePathItem(self,name):
        return str(name).translate(string.maketrans("",""),"\\/")

    def pack(self,absList,fileHandler):
        if len(absList)<=0:
            raise MaKaCError( _("no abstract to pack"))
        for abstract in absList:
            abstractDirName="abstract-%04d"%(int(abstract.getId()))
            if abstract.getAttachments() is not None :
                for res in abstract.getAttachments().values():
                    fileHandler.add("%s/%s-%s"%(abstractDirName, res.getId(), res.getFileName()), res.getFilePath())
        fileHandler.close()
        return fileHandler.getPath()

class ContribPacker:
    """
    """

    def __init__(self,conf):
        self._conf=conf
        self._items=0

    def getItems(self):
        return self._items

    def _normalisePathItem(self,name):
        return str(name).translate(string.maketrans("",""),"\\/")

    def pack(self, contribList=[], fileHandler=None):
        if len(contribList) <= 0:
            raise MaKaCError(_("no contribution to pack"))
        for contrib in contribList:
            contribDirName = "%s_%s" % (contrib.getId(), contrib.getTitle())
            for material in contrib.getAllMaterialList():
                for res in material.getResourceList():
                    if isinstance(res, conference.LocalFile):
                        self._items += 1
                        fileHandler.add("%s/%s/%s-%s-%s" % (self._normalisePathItem(contribDirName),
                                                            self._normalisePathItem(material.getTitle()),
                                                            self._normalisePathItem(contrib.getId()),
                                                            self._normalisePathItem(res.getId()),
                                                            self._normalisePathItem(res.getFileName())),
                                        res.getFilePath())
        fileHandler.close()
        return fileHandler.getPath()


class ConferencePacker:

    def __init__(self, conf, aw):
        self._conf = conf
        self._confDirName = "%s" % self._normalisePathItem(self._conf.getTitle().strip())
        self._aw = aw
        self._items = 0

    def getItems(self):
        return self._items

    def _normalisePathItem(self, name):
        return str(name).translate(string.maketrans("", ""), "\\/")

    def _addMaterials(self, element, spkList, dayDirName="", parentDirName="", elementDirName="", materialTypes=[], mainResource=False, fromDate="", fileHandler=None):
        if element.getAllMaterialList() is not None:
            for mat in element.getAllMaterialList():
                # either "other" was selected, or this type is in the list of desired ones
                resources = []
                if "other" in materialTypes or mat.getTitle().lower() in materialTypes:
                    resources = [mat.getMainResource()] if mainResource else mat.getResourceList()
                for resource in resources:
                    # URLs cannot be packed, only local files
                    if isinstance(resource, conference.LocalFile) and resource.canAccess(self._aw):
                        if fromDate == "" or resource.getCreationDate().strftime("%Y-%m-%d") >= fromDate.strftime("%Y-%m-%d"):
                            self._items += 1
                            fileHandler.add("%s-%s%s" % (os.path.join(self._confDirName,
                                                                      dayDirName,
                                                                      parentDirName,
                                                                      elementDirName,
                                                                      self._normalisePathItem(mat.getTitle())),
                                                         "%s-" % spkList if spkList else "",
                                                         self._normalisePathItem(resource.getFileName())),
                                            resource.getFilePath())

    def pack(self, materialTypes=[], days=[], mainResource=False, fromDate="", fileHandler=None, sessions=[]):
        if fromDate != "":
            [day, month, year] = fromDate.split(" ")
            fromDate = datetime(int(year), int(month), int(day))

        di = self._conf.getSchedule().getAdjustedStartDate()
        confED = self._conf.getSchedule().getAdjustedEndDate()
        ed = confED.replace(hour=23, minute=59, second=59)
        while di <= ed:
            entries = self._conf.getSchedule().getEntriesOnDay(di)
            if len(entries) > 0:
                dirName = "%s" % di.strftime("%Y%m%d_%A")
                for entry in entries:
                    if isinstance(entry, schedule.LinkedTimeSchEntry) and isinstance(entry.getOwner(), conference.Contribution):
                        if format_date(di, format='dMMMMyyyy') in days:
                            contrib = entry.getOwner()
                            self._packContrib(contrib, dirName, "", materialTypes, days, mainResource, fromDate, fileHandler)
                            for subcontrib in contrib.getSubContributionList():
                                self._packSubContrib(subcontrib, dirName, "", materialTypes, days, mainResource, fromDate, fileHandler)
                    elif isinstance(entry, schedule.LinkedTimeSchEntry) and isinstance(entry.getOwner(), conference.SessionSlot) \
                            and (entry.getOwner().getSession().getId() in sessions):
                        self._packSessionSlot(entry.getOwner(), dirName, materialTypes, days, mainResource, fromDate, fileHandler)
            di += timedelta(days=1)

        self._addMaterials(self._conf, "", "", "", "", materialTypes, mainResource, fromDate, fileHandler)

        fileHandler.close()
        return fileHandler.getPath()

    def _packContrib(self, contrib, dayDirName, slotDirName="", materialTypes=[], days=[], mainResource=False, fromDate="", fileHandler=None):

        # speakers should be added to filename, if they exist
        if len(contrib.getSpeakerList()) > 0:
            spk = "-%s" % self._normalisePathItem(contrib.getSpeakerList()[0].getFamilyName().lower())
        else:
            spk = ""

        dirName = "%s_%s" % (contrib.getAdjustedStartDate().strftime("%H%M"), contrib.getTitle())
        self._addMaterials(contrib, spk, dayDirName, slotDirName, dirName, materialTypes, mainResource, fromDate, fileHandler)

    def _packSubContrib(self, subContrib, dayDirName, slotDirName="", materialTypes=[], days=[], mainResource=False, fromDate="", fileHandler=None):

        # speakers should be added to filename, if they exist
        if len(subContrib.getSpeakerList()) > 0:
            spk = "-%s" % self._normalisePathItem(subContrib.getSpeakerList()[0].getFamilyName().lower())
        else:
            spk = ""

        contrib = subContrib.getContribution()
        dirName = "%s_%s" % (contrib.getAdjustedStartDate().strftime("%H%M"), contrib.getTitle())
        self._addMaterials(subContrib, spk, dayDirName, slotDirName, os.path.join(dirName, subContrib.getTitle()), materialTypes, mainResource, fromDate, fileHandler)

    def _packSessionSlot(self, sessionSlot, dayDirName, materialTypes=[], days=[], mainResource=False, fromDate="", fileHandler=None):

        # speakers should be added to filename, if they exist
        if len(sessionSlot.getConvenerList()) > 0:
            spk = "-%s" % self._normalisePathItem(sessionSlot.getConvenerList()[0].getFamilyName().lower())
        else:
            spk = ""

        dirName = "%s_%s" % (sessionSlot.getAdjustedStartDate().strftime("%H%M"), sessionSlot.getSession().getTitle())

        self._addMaterials(sessionSlot, spk, dayDirName, "", dirName, materialTypes, mainResource, fromDate, fileHandler)

        for entry in sessionSlot.getSchedule().getEntries():
            if isinstance(entry, schedule.LinkedTimeSchEntry) and isinstance(entry.getOwner(), conference.Contribution):
                contrib = entry.getOwner()
                self._packContrib(contrib, dayDirName, dirName, materialTypes, days, mainResource, fromDate, fileHandler)
                for subcontrib in contrib.getSubContributionList():
                    self._packSubContrib(subcontrib, dayDirName, dirName, materialTypes, days, mainResource, fromDate, fileHandler)

class PDFPagesCounter:

    def countPages(filepath):
        data = ''
        for line in file(filepath, 'rb'):
            if data:
                data.append(line)
            if '/Type/Pages' in line or '/Type /Pages' in line:
                data = [line]
            if 'endobj' in line and data:
                data = ''.join(data)
                #if '/Parent' in data:
                #    print "dat:---------------\n%s"%line
                #    data = ''
                #    continue
                pos = data.find('/Count')+7
                result = "%s"%data[pos:].split()[0].split('/')[0].replace('>>','')
                if result.strip() == "":
                    result = "0"
                return result
        return "0"
    countPages = staticmethod(countPages)

class ProceedingsPacker:
    """
    """

    def __init__(self,conf):
        self._conf=conf
        self._items=0

    def getItems(self):
        return self._items

    def _normalisePathItem(self,name):
        return str(name).translate(string.maketrans("",""),"\\/")

    def pack(self, fileHandler=None):
        if self._conf.getTrackList() != []:
            # Get every contribution order by track and by scheduled
            trackOrder=[]
            trackDict={}
            for track in self._conf.getTrackList():
                trackDict[track.getId()]=[]
                trackOrder.append(track)
            # Get contribs with papers
            for entry in self._conf.getSchedule().getEntries():
                if isinstance(entry,schedule.LinkedTimeSchEntry) and \
                        isinstance(entry.getOwner(),conference.SessionSlot):
                    slot=entry.getOwner()
                    for slotEntry in slot.getSchedule().getEntries():
                        if isinstance(slotEntry,schedule.LinkedTimeSchEntry) and isinstance(slotEntry.getOwner(),conference.Contribution):
                            contrib = slotEntry.getOwner()
                            if contrib.getPaper() is not None:
                                mr= contrib.getPaper().getMainResource()
                                if mr is not None and isinstance(mr,conference.LocalFile):
                                    track = contrib.getTrack()
                                    if track is not None:
                                        trackDict[track.getId()].append(contrib)
                elif isinstance(entry,schedule.LinkedTimeSchEntry) and \
                        isinstance(entry.getOwner(),conference.Contribution):
                    contrib = entry.getOwner()
                    if contrib.getPaper() is not None:
                        mr= contrib.getPaper().getMainResource()
                        if mr is not None and isinstance(mr,conference.LocalFile):
                            track = contrib.getTrack()
                            if track is not None:
                                trackDict[track.getId()].append(contrib)
            contribDictNPages = {}
            i = 0
            i += 1
            # Get papers
            for track in trackOrder:
                # Get Chapter Separator
                pdf = ProceedingsChapterSeparator(track)
                fileHandler.addNewFile("%04d-CHAPTER_SEPARATOR.pdf"%i, pdf.getPDFBin())
                self._items += 1
                i += 1
                for contrib in trackDict[track.getId()]:
                    paperName="%04d-%s.pdf"%(i,self._normalisePathItem(contrib.getTitle()))
                    mr= contrib.getPaper().getMainResource()
                    fileHandler.add(paperName, mr.getFilePath())
                    self._items += 1
                    contribDictNPages[contrib.getId()] = int(PDFPagesCounter.countPages(mr.getFilePath()))
                    i += 1
            # Get TOC
            pdf = ProceedingsTOC(self._conf, trackDict=trackDict, trackOrder=trackOrder, npages=contribDictNPages)
        else:
            contribDictNPages = {}
            contribList=[]
            i = 0
            i += 1
            for entry in self._conf.getSchedule().getEntries():
                if isinstance(entry,schedule.LinkedTimeSchEntry) and \
                        isinstance(entry.getOwner(),conference.SessionSlot):
                    slot=entry.getOwner()
                    for slotEntry in slot.getSchedule().getEntries():
                        if isinstance(slotEntry,schedule.LinkedTimeSchEntry) and isinstance(slotEntry.getOwner(),conference.Contribution):
                            contrib = slotEntry.getOwner()
                            if contrib.getPaper() is not None:
                                mr= contrib.getPaper().getMainResource()
                                if mr is not None and isinstance(mr,conference.LocalFile):
                                    contribList.append(contrib)
                                    paperName="%04d-%s.pdf"%(i,self._normalisePathItem(contrib.getTitle()))
                                    mr= contrib.getPaper().getMainResource()
                                    fileHandler.add(paperName, mr.getFilePath())
                                    self._items += 1
                                    contribDictNPages[contrib.getId()] = int(PDFPagesCounter.countPages(mr.getFilePath()))
                                    i += 1
                elif isinstance(entry,schedule.LinkedTimeSchEntry) and \
                        isinstance(entry.getOwner(),conference.Contribution):
                    contrib = entry.getOwner()
                    if contrib.getPaper() is not None:
                        mr= contrib.getPaper().getMainResource()
                        if mr is not None and isinstance(mr,conference.LocalFile):
                            contribList.append(contrib)
                            paperName="%04d-%s.pdf"%(i,self._normalisePathItem(contrib.getTitle()))
                            mr= contrib.getPaper().getMainResource()
                            fileHandler.add(paperName, mr.getFilePath())
                            self._items += 1
                            contribDictNPages[contrib.getId()] = int(PDFPagesCounter.countPages(mr.getFilePath()))
                            i += 1
            # Get TOC
            pdf = ProceedingsTOC(self._conf, contribList=contribList, npages=contribDictNPages)

        i = 0
        fileHandler.addNewFile("%04d-TOC.pdf"%i, pdf.getPDFBin())
        self._items += 1

        fileHandler.close()
        return fileHandler.getPath()


class ReviewingPacker:

    """
        Package the reviewing materials for the accepted papers
    """

    def __init__(self, conf):
        self._conf = conf
        self._confDirName = "%s" % self._normalisePathItem(self._conf.getTitle().strip())
        self._items = 0

    def getItems(self):
        return self._items

    def _normalisePathItem(self, name):
        return str(name).translate(string.maketrans("",""),"\\/")

    def pack(self, fileHandler=None):
        for contribution in self._conf.getContributionList():
            reviewingStatus = contribution.getReviewManager().getLastReview().getRefereeJudgement().getJudgement()
            if reviewingStatus == "Accept":
                dirName = "%s" % self._normalisePathItem(contribution.getTitle().strip())
                self._packContribution(contribution, dirName, fileHandler)

        fileHandler.close()
        return fileHandler.getPath()

    def _packContribution(self, contribution, dirName="", fileHandler=None):

        for mat in contribution.getReviewManager().getLastReview().getMaterials():
            for res in mat.getResourceList():
                self._items += 1
                fileHandler.add("%s" % (os.path.join(self._confDirName,
                                                     self._normalisePathItem(contribution.getId()) + "-" + dirName,
                                                     self._normalisePathItem(res.getFileName()))),
                                        res.getFilePath())


class RegistrantPacker:
    """
    """

    def __init__(self,conf):
        self._conf=conf
        self._items=0

    def getItems(self):
        return self._items

    def _normalisePathItem(self,name):
        return str(name).translate(string.maketrans("",""),"\\/")

    def pack(self,regList=[], fileHandler=None):
        if len(regList)<=0:
            raise MaKaCError( _("no registrant to pack"))
        for registrant in regList:
            for attachment in registrant.getAttachmentList():
                if isinstance(attachment,conference.LocalFile):
                    self._items += 1
                    fileHandler.add("%s/%s-%s-%s"%(\
                        self._normalisePathItem(registrant.getId()),
                        self._normalisePathItem(registrant.getId()),
                        self._normalisePathItem(attachment.getId()),
                        self._normalisePathItem(attachment.getFileName())),
                    attachment.getFilePath())
        fileHandler.close()
        return fileHandler.getPath()
