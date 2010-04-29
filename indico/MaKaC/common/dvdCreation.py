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

import traceback, string
import sys
import shutil, os
from persistent import Persistent
from MaKaC.webinterface.pages import conferences
from MaKaC.webinterface import urlHandlers
from MaKaC.common.Configuration import Config
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC import conference, schedule
from MaKaC.common.timerExec import HelperTaskList, task, obj
from MaKaC.common.contribPacker import ZIPFileHandler
from MaKaC.errors import MaKaCError
from MaKaC.webinterface.mail import GenericMailer, GenericNotification
import MaKaC.common.info as info
from MaKaC.i18n import _

class OfflineWebsiteCreator(obj):

    def __init__(self, rh, conf):
        obj.__init__(self)
        self._rh=rh
        self._conf=conf
        self._outputFileName=""
        self._toUser=rh._getUser()
        self._fileHandler=None

    def _getFileExtension(self, name):
        fileExtension = os.path.splitext( name )[1]
        if fileExtension != "":
            fileExtension = fileExtension[1:]
        return fileExtension

    def _getImagesList(self):
        imgFiles={}
        systemIcons=Config.getInstance().getSystemIcons()
        for icon in systemIcons.keys():
            imgFiles[icon] = "./images/%s"%systemIcons[icon]
        logo = self._conf.getLogo()
        imgFiles["logo"] = ""
        if logo is not None:
            logoName = "logo.%s"%self._getFileExtension(logo.getFileName())
            imgFiles["logo"] = "./images/%s"%logoName
        return imgFiles

    def _getAllImages(self, newImagesPath):
        # copy every images in resources/images
        imagesPath = Config.getInstance().getImagesDir()
        for img in os.listdir(imagesPath):
            if os.path.isfile(os.path.join(imagesPath, img)):
                newImgPath=os.path.join(newImagesPath, os.path.basename(img))
                file=open(os.path.join(imagesPath, os.path.basename(img)), "rb")
                self._fileHandler.addNewFile(newImgPath, file.read())
        # Logo
        logo = self._conf.getLogo()
        if logo is not None:
            logoName = "logo.%s"%self._getFileExtension(logo.getFileName())
            logoPath = os.path.join(newImagesPath, logoName)
            self._fileHandler.add(logoPath, logo.getFilePath())

    def _publicFile(self, path):
        filename=os.path.basename(path)
        if self._fileHandler is not None and \
                isinstance(self._fileHandler, ZIPFileHandler) and \
                not filename.lower().endswith(".zip"):
            filename="%s.zip"%filename
        try:
            shutil.copyfile(path, os.path.join(Config.getInstance().getPublicDir(), filename))
        except:
            raise MaKaCError( _("It is not possible to copy the offline website's zip file in the folder \"results\" to publish the file. \
                    Please contact with the system administrator"))
        return filename

    def _sendEmail(self, ofu):
        text = _("""
                    Offline website creation for your event
                    was finished and you can recover the zip file from
                    the following URL:
                    <%s>

                    Thanks for using Indico

                    --
                    Indico
                    """)%ofu
        maildata = { "fromAddr": info.HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail(), "toList": [self._toUser.getEmail()], "subject": _("[Indico] Offline website creation done"), "body": text }
        GenericMailer.send(GenericNotification(maildata))

    def _sendErrorEmail(self, e):
        ty, ex, tb = sys.exc_info()
        tracebackList = traceback.format_list( traceback.extract_tb( tb ) )
        text = _("""
                    Offline website creation for the [event:%s] had caused 
                    an error while running the task.

                    - Request from user: %s <%s>

                    - Details of the exception: 
                        %s

                    - Traceback:

                        %s

                    --

                    <Indico support> indico-project @ cern.ch
                    """)%(self._conf.getId(), self._toUser.getFullName(), self._toUser.getEmail(), e, "\n".join( tracebackList ))
        maildata = { "fromAddr": HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail(), "toList": [HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()], "subject": _("[Indico] Error in task: Offline website creation"), "body": text }
        GenericMailer.send(GenericNotification(maildata))

    def _normalisePath(self,path):
        forbiddenChars=string.maketrans(" /:()*?<>|\"","___________")
        path=path.translate(forbiddenChars)
        return path
    
    
class ConferenceOfflineCreator(OfflineWebsiteCreator):

    def _getSubdir(self, pars):
        aux = {}
        for par in pars.keys():
            aux[par] = ".%s"%pars[par]
        return aux
        

    def run( self, fileHandler=None ):
        publicFileURL = ""
        try:
            #print "[DVD] Creating offline site . . .",
            if fileHandler is None:
                self._fileHandler=ZIPFileHandler()
            else:
                self._fileHandler=fileHandler
            # Folder with the DVD
            dvdPath = "Conference-%s"%self._normalisePath(self._conf.getTitle())
            self._fileHandler.addDir(dvdPath)

            # Folder with the images
            imagesPath=os.path.join(dvdPath, "images")
            self._fileHandler.addDir(imagesPath)

            # Get all the images
            imagesPaths=self._getImagesList()
            self._getAllImages(imagesPath)
            #print ".",

            # CSS Style
            fname = os.path.join(dvdPath, "css", Config.getInstance().getCssStylesheetName())
            cssFile = open(os.path.join(Config.getInstance().getHtdocsDir(), "css", Config.getInstance().getCssStylesheetName()), "rb")
            self._fileHandler.addNewFile(fname, cssFile.read())
            cssFile.close()

            commonCSSFile = open(os.path.join(Config.getInstance().getHtdocsDir(), "css", "common.css"))
            self._fileHandler.addNewFile(os.path.join(dvdPath, "css", "common.css"), commonCSSFile.read())
            commonCSSFile.close()

            
            # Index web page for a conference + material/resources
            fname = os.path.join(dvdPath,urlHandlers.UHStaticConferenceDisplay.getRelativeURL())
            par = imagesPaths
            p = conferences.WPConferenceStaticDisplay( self._rh, self._conf, par )
            html = p.display()
            self._fileHandler.addNewFile(fname, html)
            materialList=self._conf.getAllMaterialList()
            if materialList is not None:
                for mat in materialList:
                    if len(mat.getResourceList()) > 1 or len(mat.getResourceList()) == 0:
                        fname = os.path.join(dvdPath, urlHandlers.UHStaticMaterialDisplay.getRelativeURL(mat, escape=False))
                        p = conferences.WPMaterialStaticDisplay( self._rh, mat, par )
                        html = p.display()
                        self._fileHandler.addNewFile(fname, html)
                    for res in mat.getResourceList():
                        if isinstance(res,conference.LocalFile):
                            fname = os.path.join(dvdPath, urlHandlers.UHStaticResourceDisplay.getRelativeURL(res, escape=False))
                            self._fileHandler.addNewFile(fname, res.readBin())
            #print ".",

            # Scientific programme page
            fname = os.path.join(dvdPath,urlHandlers.UHStaticConferenceProgram.getRelativeURL())
            par = imagesPaths
            p = conferences.WPConferenceStaticProgram( self._rh, self._conf, par )
            html = p.display()
            self._fileHandler.addNewFile(fname, html)
            #print ".",

            # AbstractBook
            fname = os.path.join(dvdPath,urlHandlers.UHStaticConfAbstractBook.getRelativeURL())
            from MaKaC.PDFinterface.conference import AbstractBook
            pdf = AbstractBook(self._conf,self._rh.getAW(), "")
            data = pdf.getPDFBin()
            self._fileHandler.addNewFile(fname, data)
            #print ".",

            # Author index page
            fname = os.path.join(dvdPath,urlHandlers.UHStaticConfAuthorIndex.getRelativeURL())
            par = imagesPaths
            p = conferences.WPStaticAuthorIndex( self._rh, self._conf, par )
            html = p.display()
            self._fileHandler.addNewFile(fname, html)
            #print ".",

            # Get every contribution order by track and by scheduled
            trackDict={}
            for track in self._conf.getTrackList():
                trackDict[track.getId()]=[]
                
            for session in self._conf.getSessionList():
                for slotEntry in session.getSchedule().getEntries():
                    slot = slotEntry.getOwner()
                    for contribEntry in slot.getSchedule().getEntries():
                        contrib = contribEntry.getOwner()
                        if isinstance(contribEntry, schedule.LinkedTimeSchEntry):
                            track = contrib.getTrack()
                            if track is not None:
                                trackDict[track.getId()].append(contrib)
            #print ".",
            
            # Contribution list page
            fname = os.path.join(dvdPath,urlHandlers.UHStaticContributionList.getRelativeURL())
            par = imagesPaths
            p = conferences.WPStaticContributionList( self._rh, self._conf, par, trackDict)
            html = p.display()
            self._fileHandler.addNewFile(fname, html)
            #print ".",

            # ----- Create tracks folders, materials and contributions pages
            par = self._getSubdir(imagesPaths)
            for track in self._conf.getTrackList():
                trackDir=os.path.join(dvdPath, track.getTitle().replace(" ","_"))
                # Track folder
                self._fileHandler.addDir(trackDir)
                # Track contribution list
                fname = os.path.join(dvdPath,urlHandlers.UHStaticTrackContribList.getRelativeURL(track, escape=False))
                p = conferences.WPTrackStaticContribList( self._rh, track, imagesPaths, trackDict )
                html = p.display()
                self._fileHandler.addNewFile(fname, html)
                # Contribs
                for contrib in track.getContributionList():
                    fname = os.path.join(dvdPath,urlHandlers.UHStaticContributionDisplay.getRelativeURL(contrib, escape=False))
                    p = conferences.WPContributionStaticDisplay( self._rh, contrib, par )
                    html = p.display()
                    self._fileHandler.addNewFile(fname, html)
                    materialList=contrib.getAllMaterialList()
                    if materialList is not None:
                        for mat in materialList:
                            if len(mat.getResourceList()) > 1 or len(mat.getResourceList()) == 0:
                                fname = os.path.join(trackDir, urlHandlers.UHStaticMaterialDisplay.getRelativeURL(mat, escape=False))
                                p = conferences.WPMaterialStaticDisplay( self._rh, mat, par )
                                html = p.display()
                                self._fileHandler.addNewFile(fname, html)
                            for res in mat.getResourceList():
                                if isinstance(res,conference.LocalFile):
                                    fname = os.path.join(trackDir, urlHandlers.UHStaticResourceDisplay.getRelativeURL(res))
                                    self._fileHandler.addNewFile(fname, res.readBin())
                #print ".",
            

            # ------ Other contributions not within a track -------
            otherContribsDir=os.path.join(dvdPath, "other_contributions")
            # Other Contribs folder
            self._fileHandler.addDir(otherContribsDir)
            for contrib in self._conf.getContributionList():
                if contrib.getTrack() is None:
                    fname = os.path.join(dvdPath,urlHandlers.UHStaticContributionDisplay.getRelativeURL(contrib, escape=False))
                    p = conferences.WPContributionStaticDisplay( self._rh, contrib, par )
                    html = p.display()
                    self._fileHandler.addNewFile(fname, html)
                    materialList=contrib.getAllMaterialList()
                    if materialList is not None:
                        for mat in materialList:
                            if len(mat.getResourceList()) > 1 or len(mat.getResourceList()) == 0:
                                fname = os.path.join(otherContribsDir, urlHandlers.UHStaticMaterialDisplay.getRelativeURL(mat, escape=False))
                                p = conferences.WPMaterialStaticDisplay( self._rh, mat, par )
                                html = p.display()
                                self._fileHandler.addNewFile(fname, html)
                            for res in mat.getResourceList():
                                if isinstance(res,conference.LocalFile):
                                    fname = os.path.join(otherContribsDir, urlHandlers.UHStaticResourceDisplay.getRelativeURL(res))
                                    self._fileHandler.addNewFile(fname, res.readBin())
                    #print ".",

            # Timetable
            fname = os.path.join(dvdPath,urlHandlers.UHStaticConferenceTimeTable.getRelativeURL())
            par = imagesPaths
            p = conferences.WPConferenceStaticTimeTable( self._rh, self._conf, par )
            html = p.display()
            self._fileHandler.addNewFile(fname, html)
            #print ".",

            # Session in Timetable
            sessionsDir=os.path.join(dvdPath, "sessions")
            par = self._getSubdir(imagesPaths)
            for session in self._conf.getSessionList():
                fname = os.path.join(dvdPath,urlHandlers.UHStaticSessionDisplay.getRelativeURL(session))
                p = conferences.WPSessionStaticDisplay( self._rh, session, par )
                html = p.display()
                self._fileHandler.addNewFile(fname, html)
                materialList=session.getAllMaterialList()
                if materialList is not None:
                    for mat in materialList:
                        if len(mat.getResourceList()) > 1 or len(mat.getResourceList()) == 0:
                            fname = os.path.join(sessionsDir, urlHandlers.UHStaticMaterialDisplay.getRelativeURL(mat, escape=False))
                            p = conferences.WPMaterialStaticDisplay( self._rh, mat, par )
                            html = p.display()
                            self._fileHandler.addNewFile(fname, html)
                        for res in mat.getResourceList():
                            if isinstance(res,conference.LocalFile):
                                fname = os.path.join(sessionsDir, urlHandlers.UHStaticResourceDisplay.getRelativeURL(res))
                                self._fileHandler.addNewFile(fname, res.readBin())

            self._fileHandler.close()
            
            #print "[DONE]\nmaking public the DVD...",
            self._outputFileName=self._publicFile(self._fileHandler.getPath())
            #print "[DONE]"
            publicFileURL = "%s/%s"%(Config.getInstance().getPublicURL(), self._outputFileName)
            #print "sending email...",
            self._sendEmail(publicFileURL)
            #print "[DONE]"
        except Exception, e:
            #print "[ERROR]"
            self._sendErrorEmail(e)
        self._fileHandler=None
        #print "---task finished---"
        return publicFileURL

class MeetingOfflineCreator(OfflineWebsiteCreator):
    
    def getRootDirPars(self, target, pars):
        rootDir="."
        if not isinstance(target, conference.Conference):
            rootDir="%s/.."%rootDir
            owner=target.getOwner()
            while not isinstance(owner, conference.Conference):
                rootDir="%s/.."%rootDir
                owner=owner.getOwner()
        aux = {}
        for par in pars.keys():
            aux[par] = "%s/%s"%(rootDir,pars[par])
        return aux
    
    def run( self, fileHandler=None ):
        publicFileURL = ""
        try:
            if fileHandler is None:
                self._fileHandler=ZIPFileHandler()
            else:
                self._fileHandler=fileHandler
            dvdPath = "Meeting-%s"%self._normalisePath(self._conf.getTitle())
            self._fileHandler.addDir(dvdPath)

            # Folder with the images
            imagesPath=os.path.join(dvdPath, "images")
            self._fileHandler.addDir(imagesPath)

            # Get all the images
            imagesPaths=self._getImagesList()
            self._getAllImages(imagesPath)
            #print ".",

            # CSS Style
            fname = os.path.join(dvdPath, "css", Config.getInstance().getCssStylesheetName())
            cssFile = open(os.path.join(Config.getInstance().getHtdocsDir(), "css", Config.getInstance().getCssStylesheetName()), "rb")
            self._fileHandler.addNewFile(fname, cssFile.read())
            cssFile.close()

            commonCSSFile = open(os.path.join(Config.getInstance().getHtdocsDir(), "css", "common.css"))
            self._fileHandler.addNewFile(os.path.join(dvdPath, "css", "common.css"), commonCSSFile.read())
            commonCSSFile.close()
            
            # Index web page for a conference + material/resources
            fname = os.path.join(dvdPath,urlHandlers.UHStaticConferenceDisplay.getRelativeURL())
            par = imagesPaths
            p = conferences.WPXSLMeetingStaticDisplay( self._rh, self._conf, par )
            html = p.display()
            self._fileHandler.addNewFile(fname, html)
            materialList=self._conf.getAllMaterialList()
            if materialList is not None:
                for mat in materialList:
                    if len(mat.getResourceList()) != 1:
                        paraux=self.getRootDirPars(mat, par)
                        fname = os.path.join(dvdPath, urlHandlers.UHMStaticMaterialDisplay.getRelativeURL(mat, escape=False))
                        p = conferences.WPMMaterialStaticDisplay( self._rh, mat, paraux )
                        html = p.display()
                        self._fileHandler.addNewFile(fname, html)
                    for res in mat.getResourceList():
                        if isinstance(res,conference.LocalFile):
                            fname = os.path.join(dvdPath, urlHandlers.UHMStaticResourceDisplay.getRelativeURL(res))
                            self._fileHandler.addNewFile(fname, res.readBin())

            # Material pages for the contributions in the meeting
            for contrib in self._conf.getContributionList():
                if contrib.isScheduled():
                    for mat in contrib.getAllMaterialList():
                        if len(mat.getResourceList()) != 1:
                            fname = os.path.join(dvdPath, urlHandlers.UHMStaticMaterialDisplay.getRelativeURL(mat, escape=False))
                            paraux=self.getRootDirPars(mat, par)
                            p = conferences.WPMMaterialStaticDisplay( self._rh, mat, paraux )
                            try:
                                html = p.display()
                            except Exception, e:
                                continue
                            self._fileHandler.addNewFile(fname, html)
                        for res in mat.getResourceList():
                            if isinstance(res,conference.LocalFile):
                                fname = os.path.join(dvdPath, urlHandlers.UHMStaticResourceDisplay.getRelativeURL(res, escape=False))
                                try:
                                    self._fileHandler.addNewFile(fname, res.readBin())
                                except Exception, e:
                                    continue
                    for subcont in contrib.getSubContributionList():
                        for mat in subcont.getAllMaterialList():
                            if len(mat.getResourceList()) != 1:
                                paraux=self.getRootDirPars(mat, par)
                                fname = os.path.join(dvdPath, urlHandlers.UHMStaticMaterialDisplay.getRelativeURL(mat, escape=False))
                                p = conferences.WPMMaterialStaticDisplay( self._rh, mat, paraux )
                                try:
                                    html = p.display()
                                except Exception, e:
                                    continue
                                self._fileHandler.addNewFile(fname, html)
                            for res in mat.getResourceList():
                                if isinstance(res,conference.LocalFile):
                                    fname = os.path.join(dvdPath, urlHandlers.UHMStaticResourceDisplay.getRelativeURL(res, escape=False))
                                    try:
                                        self._fileHandler.addNewFile(fname, res.readBin())
                                    except Exception, e:
                                        continue
                        
                        

            self._fileHandler.close()
            
            self._outputFileName=self._publicFile(self._fileHandler.getPath())
            publicFileURL = "%s/%s"%(Config.getInstance().getPublicURL(), self._outputFileName)
            self._sendEmail(publicFileURL)
        except Exception, e:
            self._sendErrorEmail(e)
        self._fileHandler=None
        return publicFileURL
    
class RHWrapper(Persistent):

    def __init__(self, rh):
        self._user = rh._getUser()
        self._websession=rh._getSession()
        self._aw = rh.getAW()
        self._wf=rh.getWebFactory()

    def _getUser(self):
        return self._user

    def _getSession(self):
        return self._websession

    def getAW(self):
        return self._aw

    def getWebFactory(self):
        return self._wf

    def getCurrentURL(self):
        return ""
    
class DVDCreation:

    def __init__(self, rh, conf, wf):
        self._rh=rh
        self._conf=conf
        self._wf=wf

    def create(self):
        # Create a wrapper for the RH
        rhw = RHWrapper(self._rh)
        # Instantiate a dvd creator
        if self._wf is None:
            dvdCreator = ConferenceOfflineCreator(rhw, self._conf)
        else:
            dvdCreator = MeetingOfflineCreator(rhw, self._conf)
        dvdCreator.setId("OffLineWebsiteCreator")
        
        # Create a task for the DVD Creator
        dvdTask = task()
        dvdTask.addObj(dvdCreator)

        # Add the track to the track list
        htl = HelperTaskList.getTaskListInstance()
        htl.addTask(dvdTask)

        
