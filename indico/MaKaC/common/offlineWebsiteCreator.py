# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
import os
import re
import MaKaC.common.TemplateExec as templateEngine
from MaKaC import conference
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface import displayMgr
from MaKaC.webinterface.pages.static import WPStaticConferenceTimeTable, WPStaticConferenceProgram, \
    WPStaticContributionList, WPStaticInternalPageDisplay, \
    WPStaticAuthorIndex, WPStaticSpeakerIndex, WPStaticSessionDisplay, \
    WPStaticContributionDisplay, WPStaticConfRegistrantsList, \
    WPStaticMaterialConfDisplayBase, WPStaticSubContributionDisplay, \
    WPStaticAuthorDisplay, WPTPLStaticConferenceDisplay, \
    WPStaticConferenceDisplay
from MaKaC.common.Configuration import Config
from MaKaC.common.contribPacker import ZIPFileHandler
from MaKaC.errors import MaKaCError
from MaKaC.common import timezoneUtils, info
from MaKaC.conference import LocalFile
from MaKaC.fileRepository import OfflineRepository
from MaKaC.PDFinterface.conference import ProgrammeToPDF, TimeTablePlain, AbstractBook, ContribToPDF, \
    ConfManagerContribsToPDF
from MaKaC.common.logger import Logger
from indico.util.contextManager import ContextManager


class OfflineEvent:

    def __init__(self, rh, conf, eventType):
        self._rh = rh
        self._conf = conf
        self._eventType = eventType

    def create(self):
        if self._eventType in ("simple_event", "meeting"):
            websiteCreator = OfflineEventCreator(self._rh, self._conf, self._eventType)
        elif self._eventType == "conference":
            websiteCreator = ConferenceOfflineCreator(self._rh, self._conf)
        return websiteCreator.create()


class OfflineEventCreator(object):

    def __init__(self, rh, conf, event_type=""):
        self._rh = rh
        self._conf = conf
        self._html = ""
        self._outputFile = ""
        self._fileHandler = None
        self._mainPath = ""
        self._staticPath = ""
        self._eventType = event_type

    def create(self):
        config = Config.getInstance()
        self._fileHandler = ZIPFileHandler()

        # create the home page html
        self._create_home()

        # Create main and static folders
        self._mainPath = "OfflineWebsite-%s" % self._normalisePath(self._conf.getTitle())
        self._fileHandler.addDir(self._mainPath)
        self._staticPath = os.path.join(self._mainPath, "static")
        self._fileHandler.addDir(self._staticPath)
        # Download all the icons
        self._addFolderFromSrc(os.path.join(self._staticPath, "fonts"), os.path.join(config.getHtdocsDir(), 'fonts'))

        # Getting all materials, static files (css, images, js and vars.js.tpl)
        self._getAllMaterial()
        self._html = self._getStaticFiles(self._html)

        # Specific changes
        self._create_other_pages()

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
        # Download all files generated from SASS and static js libs
        self._downloadFiles(html, 'static/static', os.path.join(config.getHtdocsDir(), 'static'), "static")
        # Download vars.js.tpl
        self._addVarsJSTpl()
        # Replace the html link
        html = html.replace("static/JSContent.py/getVars", "static/js/vars.js")
        return html

    def _create_home(self):
        # get default/selected view
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        view = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._rh._target).getDefaultStyle()
        # if no default view was attributed, then get the configuration default
        if view == "" or not styleMgr.existsStyle(view) or view in styleMgr.getXSLStyles():
            view = styleMgr.getDefaultStyleForEventType(self._eventType)
        p = WPTPLStaticConferenceDisplay(self._rh, self._rh._target, view, self._eventType, self._rh._reqParams)
        self._html = p.display(**self._rh._getRequestParams())

    def _create_other_pages(self):
        pass

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
        """
        Downloads all the files whose URL matches with baseURL in the string html (html page); and copies the file from
        the source path (srcPath) to the target folder (dstNamePath).
        """
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

    def _addFolderFromSrc(self, dstPath, srcPath):
        for root, subfolders, files in os.walk(srcPath):
            for filename in files:
                src_filepath = os.path.join(root, filename)
                dst_dirpath = os.path.join(dstPath, root.strip(srcPath))
                dst_filepath = os.path.join(dst_dirpath, filename)
                self._fileHandler.addDir(dst_dirpath)
                if not self._fileHandler.hasFile(dst_filepath):
                    self._fileHandler.add(dst_filepath, src_filepath)

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
        repo = OfflineRepository.getRepositoryFromDB()
        filename = os.path.basename(srcPath) + ".zip"
        fd = LocalFile()
        fd.setFilePath(srcPath)
        fd.setFileName(filename)
        repo.storeFile(fd, self._conf.getId())
        return fd


class ConferenceOfflineCreator(OfflineEventCreator):

    def __init__(self, rh, conf, event_type=""):
        super(ConferenceOfflineCreator, self).__init__(rh, conf, event_type)
        self._menu_offline_items = {"overview": None,
                                    "programme": None,
                                    "timetable": None,
                                    "authorIndex": None,
                                    "speakerIndex": None,
                                    "contributionList": None,
                                    "registrants": None,
                                    "abstractsBook": None}
        self._initializeMenuItensComponents()

    def _create_home(self):
        p = WPStaticConferenceDisplay(self._rh, self._conf)
        self._html = p.display()

    def _create_other_pages(self):
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
        ContextManager.set("_menu_offline_items", self._menu_offline_items)

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
