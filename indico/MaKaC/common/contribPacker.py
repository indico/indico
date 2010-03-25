# -*- coding: utf-8 -*-
##
## $Id: contribPacker.py,v 1.14 2009/05/14 18:05:52 jose Exp $
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

#import sys
#sys.path.append("c:/development/indico/code/code")

import zipfile
import tempfile
import string, sys, os
from datetime import timedelta,datetime

from MaKaC.common.utils import utf8rep
from MaKaC.errors import MaKaCError
from MaKaC import conference
from MaKaC import schedule
from MaKaC.common.Configuration import Config
from MaKaC.PDFinterface.conference import ProceedingsTOC, ProceedingsChapterSeparator
from MaKaC.i18n import _

class ZIPFileHandler:

    def __init__(self):
        (fh,name)=tempfile.mkstemp(prefix="Indico",dir=Config.getInstance().getTempDir())
        os.fdopen(fh).close()
        try:
            self._file=zipfile.ZipFile(name,"w",zipfile.ZIP_DEFLATED)
        except:
            self._file=zipfile.ZipFile(name,"w")
        self._name=name

    def _normalisePath(self,path):
        forbiddenChars=string.maketrans(" :()*?<>|\"","__________")
        path=path.translate(forbiddenChars)
        return path

    def add(self,name,path):
        name = utf8rep(name)
        self._file.write(str(path),self._normalisePath(name))

    def addNewFile(self, name, bytes):
        name = utf8rep(name)
        self._file.writestr(name, bytes)

    def addDir(self,path):
        self.addNewFile("%s/indico_file.dat" % self._normalisePath(path), "# Indico File")

    def close(self):
        self._file.close()

    def getPath(self):
        return self._name


class ContribPacker:
    """
    """

    def __init__(self,conf):
        self._conf=conf

    def _normalisePathItem(self,name):
        return str(name).translate(string.maketrans("",""),"\\/")

    def pack(self,contribList=[],materialTypes=[],fileHandler=None):
        if len(contribList)<=0:
            raise MaKaCError( _("no contribution to pack"))
        for contrib in contribList:
            spk=""
            if len(contrib.getSpeakerList())>0:
                spk=contrib.getSpeakerList()[0].getFamilyName().lower()
            contribDirName="%s-%s"%(contrib.getId(),spk)
            if "slides" in materialTypes and contrib.getSlides() is not None:
                for res in contrib.getSlides().getResourceList():
                    if isinstance(res,conference.LocalFile):
                        fileHandler.add("%s/slides/%s-%s-%s"%(\
                            self._normalisePathItem(contribDirName),
                            self._normalisePathItem(contrib.getId()),
                            self._normalisePathItem(res.getId()),
                            self._normalisePathItem(res.getFileName())),
                        res.getFilePath())
            if "paper" in materialTypes and contrib.getPaper() is not None:
                for res in contrib.getPaper().getResourceList():
                    if isinstance(res,conference.LocalFile):
                        fileHandler.add("%s/paper/%s-%s-%s"%(\
                            self._normalisePathItem(contribDirName),
                            self._normalisePathItem(contrib.getId()),
                            self._normalisePathItem(res.getId()),
                            self._normalisePathItem(res.getFileName())),
                        res.getFilePath())
        fileHandler.close()
        return fileHandler.getPath()


class ConferencePacker:

    def __init__(self,conf,aw):
        self._conf=conf
        self._confDirName="%s"%self._normalisePathItem(self._conf.getTitle().strip())
        self._aw=aw

    def _normalisePathItem(self,name):
        return str(name).translate(string.maketrans("",""),"\\/")

    def pack(self,materialTypes=[],days=[], mainResource=False, fromDate="", fileHandler=None, sessions=[]):
        if fromDate != "":
            [ day, month, year] = fromDate.split(" ")
            fromDate = datetime(int(year),int(month),int(day))

        di=self._conf.getSchedule().getAdjustedStartDate()
        confED=self._conf.getSchedule().getAdjustedEndDate()
        ed = confED.replace(hour=23,minute=59,second=59)
        while di<=ed:
            if days == [] or days is None or di.strftime("%d%B%Y") in days:
                if len(self._conf.getSchedule().getEntriesOnDay(di)) > 0:
                    dirName = "%s"%di.strftime("%Y%m%d_%A")
                    #fileHandler.addDir("%s/%s"%(self._confDirName,dirName))
                    for entry in self._conf.getSchedule().getEntriesOnDay(di):
                        if isinstance(entry,schedule.LinkedTimeSchEntry) and isinstance(entry.getOwner(),conference.Contribution):
                            contrib=entry.getOwner()
                            self._packContrib(contrib, "", dirName, materialTypes,days,mainResource,fromDate,fileHandler)
                            for subcontrib in contrib.getSubContributionList():
                                self._packContrib(subcontrib, "", dirName, materialTypes,days,mainResource,fromDate,fileHandler)
            di+=timedelta(days=1)
        for session in self._conf.getSessionList():
            if len(sessions) == 0 or session.getId() in sessions:
                di=session.getSchedule().getAdjustedStartDate()
                sesED=session.getSchedule().getAdjustedEndDate()
                ed = sesED.replace(hour=23,minute=59,second=59)
                sessionDirName="%s"%self._normalisePathItem(session.getTitle().strip())
                while di<=ed:
                    if days == [] or days is None or di.strftime("%d%B%Y") in days:
                        for entry in session.getSchedule().getEntriesOnDay(di):
                            if isinstance(entry,schedule.LinkedTimeSchEntry) and \
                                    isinstance(entry.getOwner(),conference.SessionSlot):
                                slot=entry.getOwner()
                                slotDirName="%s"%di.strftime("%Y%m%d_%A")
                                if slot.getTitle()!="":
                                    slotDirName="%s-%s"%(slotDirName,self._normalisePathItem(slot.getTitle().strip()))
                                #fileHandler.addDir("%s/%s/%s"%(self._confDirName,sessionDirName,slotDirName))
                                for entry in slot.getSchedule().getEntries():
                                    if isinstance(entry,schedule.LinkedTimeSchEntry) and isinstance(entry.getOwner(),conference.Contribution):
                                        contrib=entry.getOwner()
                                        self._packContrib(contrib, sessionDirName, slotDirName, materialTypes,days,mainResource,fromDate,fileHandler)
                                        for subcontrib in contrib.getSubContributionList():
                                            self._packContrib(subcontrib, sessionDirName, slotDirName, materialTypes,days,mainResource,fromDate,fileHandler)
                    di+=timedelta(days=1)

        # add "root" materials as well
        # (totally hacky... a general method for adding
        # materials should be added... check copy below)

        for mat in self._conf.getAllMaterialList():

            if "other" in materialTypes or mat.getTitle().lower() in materialTypes:
                if mainResource:
                    resources = [mat.getMainResource()]
                else:
                    resources = mat.getResourceList()
            else:
                resources = []

            for resource in resources:
                # URLs cannot be packed, only local files
                if isinstance(resource, conference.LocalFile) and resource.canAccess(self._aw):
                    if fromDate == "" or resource.getCreationDate().strftime("%Y-%m-%d") >= fromDate.strftime("%Y-%m-%d"):
                        fileHandler.add("%s-%s" % (os.path.join(self._confDirName,
                                                           mat.getTitle()),
                                                           self._normalisePathItem(resource.getFileName())),
                                        resource.getFilePath())

        fileHandler.close()
        return fileHandler.getPath()

    def _packContrib(self, contrib, sessionDirName="", slotDirName="", materialTypes=[],days=[], mainResource=False, fromDate="", fileHandler=None):

        # speakers should be added to filename, if they exist
        if len(contrib.getSpeakerList()) > 0:
            spk = "-%s" % self._normalisePathItem(contrib.getSpeakerList()[0].getFamilyName().lower())
        else:
            spk = ""

        if contrib.getAllMaterialList() is not None:
            for mat in contrib.getAllMaterialList():

                # either "other" was selected, or this type is in the list of desired ones
                if "other" in materialTypes or mat.getTitle().lower() in materialTypes:
                    if mainResource:
                        resources = [mat.getMainResource()]
                    else:
                        resources = mat.getResourceList()
                else:
                    resources = []

                for resource in resources:
                    # URLs cannot be packed, only local files
                    if isinstance(resource, conference.LocalFile) and resource.canAccess(self._aw):
                        if fromDate == "" or resource.getCreationDate().strftime("%Y-%m-%d") >= fromDate.strftime("%Y-%m-%d"):
                            fileHandler.add("%s-%s%s-%s" % (os.path.join(self._confDirName,
                                                                     sessionDirName,
                                                                     slotDirName,
                                                                     self._normalisePathItem(contrib.getId())),
                                                                     mat.getTitle(),
                                                                     spk,
                                                                     self._normalisePathItem(resource.getFileName())),
                                            resource.getFilePath())


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
                i += 1
                for contrib in trackDict[track.getId()]:
                    paperName="%04d-%s.pdf"%(i,self._normalisePathItem(contrib.getTitle()))
                    mr= contrib.getPaper().getMainResource()
                    fileHandler.add(paperName, mr.getFilePath())
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
                            contribDictNPages[contrib.getId()] = int(PDFPagesCounter.countPages(mr.getFilePath()))
                            i += 1
            # Get TOC
            pdf = ProceedingsTOC(self._conf, contribList=contribList, npages=contribDictNPages)

        i = 0
        fileHandler.addNewFile("%04d-TOC.pdf"%i, pdf.getPDFBin())

        fileHandler.close()
        return fileHandler.getPath()


