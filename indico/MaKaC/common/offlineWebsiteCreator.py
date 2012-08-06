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
import shutil, os
import re
import MaKaC.common.TemplateExec as templateEngine
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface import displayMgr
from MaKaC.webinterface.pages import conferences, registrants, contributions, sessions,\
    authors
from MaKaC.common.Configuration import Config
from MaKaC.common.contribPacker import ZIPFileHandler
from MaKaC.errors import MaKaCError
from MaKaC.i18n import _
from MaKaC.common.logger import Logger
from MaKaC.common import timezoneUtils

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
        self._outputFileName = ""
        self._fileHandler = None
        self._mainPath = ""
        self._staticPath = ""
        #self._toUser = ContextManager.get('currentUser')

    def create(self):
        try:
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

            fname = os.path.join(self._mainPath, urlHandlers.UHConferenceDisplay.getStaticURL())
            self._fileHandler.addNewFile(fname, self._html)
            self._fileHandler.close()
            self._outputFileName = self._generateZipFile(self._fileHandler.getPath())
        except Exception, e:
            Logger.get('offline-website').error(str(e))
        self._fileHandler = None
        return self._outputFileName

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
        self._addMaterialFrom(self._conf, "events/%s-conference" % self._conf.getId())
        for contrib in self._conf.getContributionList():
            self._addMaterialFrom(contrib, "agenda/%s-contribution" % contrib.getId())
            if (contrib.getSubContributionList() is not None):
                for sc in contrib.getSubContributionList():
                    self._addMaterialFrom(sc, "agenda/%s-subcontribution" % sc.getId())
        for session in self._conf.getSessionList():
            self._addMaterialFrom(session, "agenda/%s-session" % session.getId())

    def _addMaterialFrom(self, target, categoryPath):
        if target.getAllMaterialList() is not None:
            for mat in target.getAllMaterialList():
                for res in mat.getResourceList():
                    dstPath = os.path.join(self._mainPath, "files", categoryPath, mat.getId(), res.getId() + "-" + res.getName())
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
            cssFile = open(cssFilename, "rb")
            for line in cssFile.readlines():
                images = re.findall(r'images/(.+?\.\w*)', line)
                for imgFilename in images:
                    imgSrcFile = os.path.join(config.getImagesDir(), imgFilename)
                    imgDstFile = os.path.join(imgPath, imgFilename)
                    self._addFileFromSrc(imgDstFile, imgSrcFile)

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

    def _generateZipFile(self, path):
        filename = os.path.basename(path)
        if self._fileHandler is not None and \
                isinstance(self._fileHandler, ZIPFileHandler) and \
                not filename.lower().endswith(".zip"):
            filename = "%s.zip" % filename
        try:
            print "ZIPFilename: %s" % filename
            shutil.copyfile(path, filename)
        except:
            # TODO: If using Scheduler, the Error to raise should be different
            raise MaKaCError(_("It is not possible to copy the offline website's zip file in the folder \"results\" to publish the file. \
                    Please contact with the system administrator"))
        return filename

class ConferenceOfflineCreator(OfflineEventCreator):

    # Menu itens allowed to be shown in offline mode
    _menu_offline_itens = {"overview" : None, \
                           "programme" : None, \
                           "timetable" : None, \
                           "authorIndex" : None, \
                           "speakerIndex" : None, \
                           "contributionList" : None, \
                           "registrants" : None,
                           "abstractsBook" : None}

    def _create(self):
        self._initializeMenuItensComponents()
        # Getting conference logo
        self._addLogo()
        # Getting all menu itens
        self._getMenuItens()
        # Getting specific pages for contributions
        for cont in self._conf.getContributionList():
            self._getContrib(cont)

        for session in self._conf.getSessionList():
            self._getSession(session)

    def _initializeMenuItensComponents(self):
        self._menu_offline_itens["programme"] = conferences.WPStaticConferenceProgram(self._rh, self._conf)
        self._menu_offline_itens["timetable"] = conferences.WPStaticConferenceTimeTable(self._rh, self._conf)
        self._menu_offline_itens["authorIndex"] = conferences.WPStaticAuthorIndex(self._rh, self._conf)
        self._menu_offline_itens["speakerIndex"] = conferences.WPStaticSpeakerIndex(self._rh, self._conf)
        self._menu_offline_itens["contributionList"] = conferences.WPStaticContributionList(self._rh, self._conf)
        self._menu_offline_itens["registrants"] = registrants.WPStaticConfRegistrantsList(self._rh, self._conf)

    def _addLogo(self):
        if self._conf.getLogo() is not None:
            logoDstPath = os.path.join(self._mainPath, Config.getInstance().getImagesBaseURL(), "logo", str(self._conf.getLogo()))
            self._fileHandler.addNewFile(logoDstPath, self._conf.getLogo().readBin())

    def _getMenuItens(self):
        menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        for link in menu.getEnabledLinkList():
            if link.isVisible():
                if isinstance(link, displayMgr.PageLink):
                    self._getInternalPage(link)
                elif not isinstance(link, displayMgr.Spacer):
                        self._getMenuSystemItem(link)

    def _getMenuSystemItem(self, link):
        if link.getName() in self._menu_offline_itens.keys():
            if self._menu_offline_itens[link.getName()] is not None:
                # TODO: remove this if clause when change the author and speaker filtering to use JavaScript
                if link.getName in ("authorIndex", "speakerIndex"):
                    html = self._menu_offline_itens[link.getName()].display(viewMode="full", selLetter="a")
                else:
                    html = self._menu_offline_itens[link.getName()].display()
                handler = getattr(urlHandlers, link.getURLHandler())
                self._addPage(html, handler)
        if (link.getName() == "abstractsBook"):
            self._addAbstractBookPDF()
        if (link.getName() == "programme"):
            self._addConferenceProgrammePDF()

    def _getInternalPage(self, link):
        page = link.getPage()
        html = conferences.WPStaticInternalPageDisplay(self._rh, self._conf, page).display()
        self._addPage(html, urlHandlers.UHInternalPageDisplay, page)

    def _addPage(self, html, rh, target=None):
        fname = os.path.join(self._mainPath, rh.getStaticURL(target))
        html = self._getStaticFiles(html)
        self._fileHandler.addNewFile(fname, html)

    def _getContrib(self, contrib):
        html = contributions.WPStaticContributionDisplay( self._rh, contrib, 0 ).display()
        self._addPage(html, urlHandlers.UHContributionDisplay, contrib)
        self._addContribPDF(contrib)

        for author in contrib.getAuthorList():
            self._getAuthor(contrib, author)
        for author in contrib.getCoAuthorList():
            self._getAuthor(contrib, author)

    def _getAuthor(self, contrib, author):
        html = authors.WPStaticAuthorDisplay(self._rh, contrib, author.getId()).display()
        self._addPage(html, urlHandlers.UHContribAuthorDisplay, author)

    def _getSession(self, session):
        html = sessions.WPStaticSessionDisplay(self._rh, session).display(activeTab="")
        self._addPage(html, urlHandlers.UHSessionDisplay, session);

        # FIX: contribs tab static link
        htmlContrib = sessions.WPStaticSessionDisplay(self._rh, session).display(activeTab="contribs")
        sessionContribfile = os.path.join(self._mainPath, urlHandlers.UHSessionDisplay.getStaticURL(session)+"contribs")
        htmlContrib = self._getStaticFiles(htmlContrib)
        self._fileHandler.addNewFile(sessionContribfile, htmlContrib)

    # --------------- PDF Files ------------
    def _addConferenceProgrammePDF(self):
        from MaKaC.PDFinterface.conference import ProgrammeToPDF
        tz = timezoneUtils.DisplayTZ(self._rh._aw, self._conf).getDisplayTZ()
        filename = os.path.join(self._mainPath, urlHandlers.UHConferenceProgramPDF.getStaticURL(self._conf))
        pdf = ProgrammeToPDF(self._conf, tz=tz)
        self._fileHandler.addNewFile(filename, pdf.getPDFBin())

    def _addAbstractBookPDF(self):
        from MaKaC.PDFinterface.conference import AbstractBook
        tz = timezoneUtils.DisplayTZ(self._rh._aw, self._conf).getDisplayTZ()
        filename = os.path.join(self._mainPath, urlHandlers.UHConfAbstractBook.getStaticURL(self._conf))
        pdf = AbstractBook(self._conf, self._rh._aw, tz=tz)
        self._fileHandler.addNewFile(filename, pdf.getPDFBin())

    def _addContribPDF(self, contrib):
        from MaKaC.PDFinterface.conference import ContribToPDF
        tz = timezoneUtils.DisplayTZ(self._rh._aw, self._conf).getDisplayTZ()
        filename = os.path.join(self._mainPath, urlHandlers.UHContribToPDF.getStaticURL(contrib))
        pdf = ContribToPDF(self._conf, contrib, tz=tz)
        self._fileHandler.addNewFile(filename, pdf.getPDFBin())

