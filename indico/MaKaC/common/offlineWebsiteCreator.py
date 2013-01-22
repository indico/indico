# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

import string
import shutil
import os
import re
import MaKaC.common.TemplateExec as templateEngine
from MaKaC import conference
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface import displayMgr
from MaKaC.webinterface.pages.static import WPTPLStaticConferenceDisplay, WPStaticConferenceDisplay, WPStaticConferenceTimeTable, WPStaticConferenceProgram, WPStaticContributionList, WPStaticInternalPageDisplay, WPStaticAuthorIndex, WPStaticSpeakerIndex, WPStaticSessionDisplay, WPStaticContributionDisplay, WPStaticConfRegistrantsList, WPStaticMaterialConfDisplayBase, WPStaticSubContributionDisplay, WPStaticAuthorDisplay
from MaKaC.common.Configuration import Config
from MaKaC.common.contribPacker import ZIPFileHandler
from MaKaC.errors import MaKaCError
from MaKaC.i18n import _
from MaKaC.common.logger import Logger
from MaKaC.common import timezoneUtils
from MaKaC.conference import LocalFile
from MaKaC.fileRepository import LocalRepository

from MaKaC.PDFinterface.conference import ProgrammeToPDF
from MaKaC.PDFinterface.conference import TimeTablePlain
from MaKaC.PDFinterface.conference import AbstractBook
from MaKaC.PDFinterface.conference import ContribToPDF
from MaKaC.PDFinterface.conference import TimeTablePlain
from MaKaC.PDFinterface.conference import ConfManagerContribsToPDF

class OfflineEvent:

    def __init__(self, rh, conf, eventType, html):
        self._rh = rh
        self._conf = conf
        self._eventType = eventType
        self._html = html

    def create(self):
        if self._eventType in ("simple_event", "meeting"):
            websiteCreator = OfflineEventCreator(self._rh, self._conf, self._html)
        elif self._eventType == "conference":
            websiteCreator = ConferenceOfflineCreator(self._rh, self._conf, self._html)
        return websiteCreator.create()


class OfflineEventCreator:

    def __init__(self, rh, conf, html):
        self._rh = rh
        self._conf = conf
        self._html = html
        self._outputFile = ""
        self._fileHandler = None
        self._mainPath = ""
        self._staticPath = ""
        # self._toUser = ContextManager.get('currentUser')

    def create(self):
        config = Config.getInstance()
        self._fileHandler = ZIPFileHandler()
        
        # Create main and static folders
        self._mainPath = "OfflineWebsite-%s" % self._normalisePath(self._conf.getTitle())
        self._fileHandler.addDir(self._mainPath)
        self._staticPath = os.path.join(self._mainPath, "static")
        self._fileHandler.addDir(self._staticPath)

        # Getting all materials, static files (css, images, js and vars.js.tpl)
        self._getAllMaterial()
        self._html = self._getStaticFiles(self._html)
        
        # Specific changes
        self._create()

        # Creating ConferenceDisplay.html file
        conferenceDisplayPath = os.path.join(self._mainPath, urlHandlers.UHConferenceDisplay.getStaticURL()) 
        self._fileHandler.addNewFile(conferenceDisplayPath, self._html)
        
        # Creating index.html file
        self._fileHandler.addNewFile("index.html", """<meta HTTP-EQUIV="REFRESH" content="0; url=%s">""" % conferenceDisplayPath)
        
        self._fileHandler.close()
        self._outputFile = self._generateZipFile(self._fileHandler.getPath())
        return self._outputFile

    def _getStaticFiles(self, html):
        config = Config.getInstance()
        # Download all images
        self._downloadFiles(html, config.getImagesBaseURL(), config.getImagesDir(), "images")
        # Download all CSS files
        self._downloadFiles(html, config.getCssBaseURL(), config.getCssDir(), "css")
        # Download all JS files
        self._downloadFiles(html, "js", config.getJSDir(), "js")
        # Download vars.js.tpl
        self._addVarsJSTpl()
        # Replace the html link
        html = html.replace("static/JSContent.py/getVars", "static/js/vars.js")
        return html

    def _create(self):
        return ""

    def _normalisePath(self, path):
        forbiddenChars = string.maketrans(" /:()*?<>|\"", "___________")
        path = path.translate(forbiddenChars)
        return path

    def _getAllMaterial(self):
        self._addMaterialFrom(self._conf, "events/conference")
        for contrib in self._conf.getContributionList():
            self._addMaterialFrom(contrib, "agenda/%s-contribution" % contrib.getId())
            if contrib.getSubContributionList():
                for sc in contrib.getSubContributionList():
                    self._addMaterialFrom(sc, "agenda/%s-subcontribution" % sc.getId())
        for session in self._conf.getSessionList():
            self._addMaterialFrom(session, "agenda/%s-session" % session.getId())

    def _addMaterialFrom(self, target, categoryPath):
        if target.getAllMaterialList():
            for mat in target.getAllMaterialList():
                for res in mat.getResourceList():
                    if isinstance(res, conference.LocalFile):
                        dstPath = os.path.join(
                            self._mainPath, "files", categoryPath, mat.getId(), res.getId() + "-" + res.getName())
                        self._addFileFromSrc(dstPath, res.getFilePath())

    def _downloadFiles(self, html, baseURL, srcPath, dstNamePath):
        dstPath = os.path.join(self._staticPath, dstNamePath)
        self._fileHandler.addDir(dstPath)
        files = re.findall(r'%s/(.+?\..+?)[?|"]' % (baseURL), html)
        for filename in files:
            srcFile = os.path.join(srcPath, filename)
            dstFile = os.path.join(dstPath, filename)
            # If a CSS File, download the images
            if (dstNamePath == "css"):
                self._addImagesFromCss(srcFile)
            self._addFileFromSrc(dstFile, srcFile)

    def _addFileFromSrc(self, dstPath, srcPath):
        if not os.path.isfile(dstPath) and os.path.isfile(srcPath):
            if not self._fileHandler.hasFile(dstPath):
                newFile = open(srcPath, "rb")
                self._fileHandler.addNewFile(dstPath, newFile.read())
                newFile.close()

    def _addImagesFromCss(self, cssFilename):
        config = Config.getInstance()
        if os.path.isfile(cssFilename):
            imgPath = os.path.join(self._staticPath, "images")
            fontPath = os.path.join(self._staticPath, "fonts")
            cssFile = open(cssFilename, "rb")
            for line in cssFile.readlines():
                images = re.findall(r'images/(.+?\.\w*)', line)
                fonts = re.findall(r'fonts/(.+?\.\w*)', line)
                for imgFilename in images:
                    imgSrcFile = os.path.join(config.getImagesDir(), imgFilename)
                    imgDstFile = os.path.join(imgPath, imgFilename)
                    self._addFileFromSrc(imgDstFile, imgSrcFile)
                for fontFilename in fonts:
                    fontSrcFile = os.path.join(config.getFontsDir(), fontFilename)
                    fontDstFile = os.path.join(fontPath, fontFilename)
                    self._addFileFromSrc(fontDstFile, fontSrcFile)

    def _addVarsJSTpl(self):
        config = Config.getInstance()
        varsPath = os.path.join(self._staticPath, "js/vars.js")
        tplFile = os.path.join(config.getTPLDir(), "js/vars.js.tpl")
        if not os.path.isfile(varsPath):
            varsDict = {}
            varsDict["__rh__"] = self._rh
            varsDict["user"] = None
            varsData = templateEngine.render(tplFile, varsDict)
            self._fileHandler.addNewFile(varsPath, varsData)

    def _generateZipFile(self, srcPath):
        repo = LocalRepository()
        filename = os.path.basename(srcPath) + ".zip"
        file = LocalFile()
        file.setFilePath(srcPath)
        file.setFileName(filename)
        repo.storeFile(file, self._conf.getId())
        return file


class ConferenceOfflineCreator(OfflineEventCreator):

    # Menu items allowed to be shown in offline mode
    _menu_offline_items = {"overview": None,
                           "programme": None,
                           "timetable": None,
                           "authorIndex": None,
                           "speakerIndex": None,
                           "contributionList": None,
                           "registrants": None,
                           "abstractsBook": None}

    def _create(self):
        self._initializeMenuItensComponents()
        # Getting conference logo
        self._addLogo()
        # Getting all menu items
        self._getMenuItems()
        # Getting conference timetable in PDF
        self._addPdf(self._conf, urlHandlers.UHConfTimeTablePDF, TimeTablePlain, **{'conf': self._conf, 'aw': self._rh._aw})
        # Generate contributions in PDF
        self._addPdf(self._conf, urlHandlers.UHContributionListToPDF, ConfManagerContribsToPDF, **{'conf': self._conf, 'contribList': self._conf.getContributionList()})

        # Getting specific pages for contributions
        for cont in self._conf.getContributionList():
            self._getContrib(cont)
            # Getting specific pages for subcontributions
            for subCont in cont.getSubContributionList():
                self._getSubContrib(subCont)

        for session in self._conf.getSessionList():
            self._getSession(session)

        # Getting material pages for conference
        self._addConferenceMaterialDisplayPages()

    def _addConferenceMaterialDisplayPages(self):
        for mat in self._conf.getAllMaterialList():
            if len(mat.getResourceList()) != 1:
                html = WPStaticMaterialConfDisplayBase(self._rh, mat).display()
                self._addPage(html, urlHandlers.UHMaterialDisplay, target=mat)

    def _initializeMenuItensComponents(self):
        self._menu_offline_items["programme"] = WPStaticConferenceProgram(self._rh, self._conf)
        self._menu_offline_items["timetable"] = WPStaticConferenceTimeTable(self._rh, self._conf)
        self._menu_offline_items["authorIndex"] = WPStaticAuthorIndex(self._rh, self._conf)
        self._menu_offline_items["speakerIndex"] = WPStaticSpeakerIndex(self._rh, self._conf)
        self._menu_offline_items["contributionList"] = WPStaticContributionList(self._rh, self._conf)
        self._menu_offline_items["registrants"] = WPStaticConfRegistrantsList(self._rh, self._conf)

    def _addLogo(self):
        if self._conf.getLogo():
            logoDstPath = os.path.join(
                self._mainPath, Config.getInstance().getImagesBaseURL(), "logo", str(self._conf.getLogo()))
            self._fileHandler.addNewFile(logoDstPath, self._conf.getLogo().readBin())

    def _getMenuItems(self):
        menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        for link in menu.getEnabledLinkList():
            if link.isVisible():
                if isinstance(link, displayMgr.PageLink):
                    self._getInternalPage(link)
                elif not isinstance(link, displayMgr.Spacer):
                    self._getMenuSystemItem(link)

    def _getMenuSystemItem(self, link):
        if link.getName() in self._menu_offline_items.keys():
            if self._menu_offline_items[link.getName()]:
                html = self._menu_offline_items[link.getName()].display()
                handler = getattr(urlHandlers, link.getURLHandler())
                self._addPage(html, handler, target=None)
        if (link.getName() == "abstractsBook"):
            self._addPdf(self._conf, urlHandlers.UHConfAbstractBook, AbstractBook, **{'conf': self._conf, 'aw': self._rh._aw})
        if (link.getName() == "programme"):
            self._addPdf(self._conf, urlHandlers.UHConferenceProgramPDF, ProgrammeToPDF, **{'conf': self._conf})

    def _getInternalPage(self, link):
        page = link.getPage()
        html = WPStaticInternalPageDisplay(self._rh, self._conf, page).display()
        self._addPage(html, urlHandlers.UHInternalPageDisplay, target=page)

    def _addPage(self, html, rh, target, **params):
        fname = os.path.join(self._mainPath, str(rh.getStaticURL(target, **params)))
        html = self._getStaticFiles(html)
        self._fileHandler.addNewFile(fname, html)

    def _getContrib(self, contrib):
        html = WPStaticContributionDisplay(self._rh, contrib, 0).display()
        self._addPage(html, urlHandlers.UHContributionDisplay, target=contrib)
        self._addPdf(contrib, urlHandlers.UHContribToPDF, ContribToPDF, **{'conf': self._conf, 'contrib': contrib})

        for author in contrib.getAuthorList():
            self._getAuthor(contrib, author)
        for author in contrib.getCoAuthorList():
            self._getAuthor(contrib, author)

    def _getSubContrib(self, subContrib):
        html = WPStaticSubContributionDisplay(self._rh, subContrib).display()
        self._addPage(html, urlHandlers.UHSubContributionDisplay, target=subContrib)

    def _getAuthor(self, contrib, author):
        try:
            html = WPStaticAuthorDisplay(self._rh, contrib, author.getId()).display()
            self._addPage(html, urlHandlers.UHContribAuthorDisplay, target=contrib, authorId=author.getId())
        except MaKaCError:
            pass

    def _getSession(self, session):
        html = WPStaticSessionDisplay(self._rh, session).display(activeTab="")
        self._addPage(html, urlHandlers.UHSessionDisplay, target=session)

        htmlContrib = WPStaticSessionDisplay(self._rh, session).display(activeTab="contribs")
        sessionContribfile = os.path.join(self._mainPath, "contribs-" + urlHandlers.UHSessionDisplay.getStaticURL(session))
        htmlContrib = self._getStaticFiles(htmlContrib)
        self._fileHandler.addNewFile(sessionContribfile, htmlContrib)
        self._addPdf(session, urlHandlers.UHConfTimeTablePDF, TimeTablePlain, **{'conf': self._conf, 'aw':
                     self._rh._aw, 'showSessions': [session.getId()]})

    def _addPdf(self, event, pdfUrlHandler, generatorClass, **generatorParams):
        tz = timezoneUtils.DisplayTZ(self._rh._aw, self._conf).getDisplayTZ()
        filename = os.path.join(self._mainPath, pdfUrlHandler.getStaticURL(event))
        pdf = generatorClass(tz=tz, **generatorParams)
        self._fileHandler.addNewFile(filename, pdf.getPDFBin())
