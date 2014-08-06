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

import itertools
import os
import re
import requests
import string
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename
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
from indico.core.config import Config
from MaKaC.common.contribPacker import ZIPFileHandler
from MaKaC.errors import MaKaCError
from MaKaC.common import timezoneUtils, info
from MaKaC.conference import LocalFile
from MaKaC.fileRepository import OfflineRepository
from MaKaC.PDFinterface.conference import ProgrammeToPDF, TimeTablePlain, AbstractBook, ContribToPDF, \
    ContribsToPDF
from indico.util.contextManager import ContextManager
from indico.util.string import remove_tags
from indico.web.assets import ie_compatibility


RE_CSS_URL = re.compile(r'url\(\s*(?P<quote>["\']?)(?!data:)(?P<url>[^\\\')]+)(?P=quote)\s*\)')
RE_QUERYSTRING = re.compile(r'\?.+$')


def _remove_qs(url):
    """Removes a cache buster (or any other query string)."""
    return RE_QUERYSTRING.sub('', url)


def _fix_url_path(path):
    """Sanitizes an URL extracted from the HTML document"""
    if path.startswith('static/'):
        # It's a path that was prefixed with baseurl
        path = path[7:]
    elif path.startswith(Config.getInstance().getBaseURL()):
        path = path[len(Config.getInstance().getBaseURL()):]
    elif path.startswith(Config.getInstance().getBaseSecureURL()):
        path = path[len(Config.getInstance().getBaseSecureURL()):]
    path = path.lstrip('/')
    path = _remove_qs(path)
    return path


class OfflineEvent:

    def __init__(self, rh, conf, eventType):
        self._rh = rh
        self._conf = conf
        self._eventType = eventType

    def create(self):
        websiteCreator = None
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
        self._failed_paths = set()
        self._css_files = set()
        self._downloaded_files = {}

    def create(self):
        config = Config.getInstance()
        self._fileHandler = ZIPFileHandler()

        # create the home page html
        self._create_home()

        # Create main and static folders
        self._mainPath = self._normalize_path(u'OfflineWebsite-{}'.format(self._conf.getTitle().decode('utf-8')))
        self._fileHandler.addDir(self._mainPath)
        self._staticPath = os.path.join(self._mainPath, "static")
        self._fileHandler.addDir(self._staticPath)
        # Add i18n js
        self._addFolderFromSrc(os.path.join(self._staticPath, 'js', 'indico', 'i18n'),
                               os.path.join(config.getHtdocsDir(), 'js', 'indico', 'i18n'))
        # Add system icons (not referenced in HTML/CSS)
        for icon in Config.getInstance().getSystemIcons().itervalues():
            self._addFileFromSrc(os.path.join(self._staticPath, 'images', icon),
                                 os.path.join(config.getHtdocsDir(), 'images', icon))
        # IE compat files (in conditional comments so BS doesn't see them)
        for path in ie_compatibility.urls():
            self._addFileFromSrc(os.path.join(self._staticPath, path.lstrip('/')),
                                 os.path.join(config.getHtdocsDir(), path.lstrip('/')))

        # Getting all materials, static files (css, images, js and vars.js.tpl)
        self._getAllMaterial()
        self._html = self._get_static_files(self._html)

        # Specific changes
        self._create_other_pages()

        # Retrieve files that were not available in the file system (e.e. js/css from plugins)
        self._get_failed_paths()
        self._failed_paths = set()

        # Retrieve files referenced in CSS files
        self._get_css_refs()

        # A custom event CSS might reference an uploaded image so we need to check for failed paths again
        self._get_failed_paths()

        # Creating ConferenceDisplay.html file
        conferenceDisplayPath = os.path.join(self._mainPath, urlHandlers.UHConferenceDisplay.getStaticURL())
        self._fileHandler.addNewFile(conferenceDisplayPath, self._html)

        # Creating index.html file
        self._fileHandler.addNewFile('index.html',
                                     '<meta http-equiv="Refresh" content="0; url=%s">' % conferenceDisplayPath)

        self._fileHandler.close()
        self._outputFile = self._generateZipFile(self._fileHandler.getPath())
        return self._outputFile

    def _get_static_files(self, html):
        config = Config.getInstance()
        soup = BeautifulSoup(html)
        scripts = set(_fix_url_path(x['src']) for x in soup.select('script[src]'))
        styles = set(_fix_url_path(x['href']) for x in soup.select('link[rel="stylesheet"]'))
        for path in itertools.chain(scripts, styles):
            src_path = os.path.join(config.getHtdocsDir(), path)
            dst_path = os.path.join(self._staticPath, path)
            if path in styles:
                self._css_files.add(path)
            if not os.path.isfile(src_path):
                self._failed_paths.add(path)
            elif path not in styles:
                self._addFileFromSrc(dst_path, src_path)
        for script in soup.select('script[src]'):
            script['src'] = os.path.join('static', _fix_url_path(script['src']))
        for style in soup.select('link[rel="stylesheet"]'):
            style['href'] = os.path.join('static', _fix_url_path(style['href']))
        return str(soup)

    def _get_failed_paths(self):
        """Downloads files that were not available in the fielystem via HTTP.
        This is the only clean way to deal with static files from plugins since otherwise
        we would have to emulate RHHtdocs.
        """
        cfg = Config.getInstance()
        # If we have the embedded webserver prefer its base url since the iptables hack does
        # not work for connections from the same machine
        base_url = cfg.getEmbeddedWebserverBaseURL() or cfg.getBaseURL()
        for path in self._failed_paths:
            dst_path = os.path.join(self._staticPath, path)
            if not self._fileHandler.hasFile(dst_path):
                response = requests.get(os.path.join(base_url, path), verify=False)
                self._downloaded_files[dst_path] = response.content
                self._fileHandler.addNewFile(dst_path, response.content)

    def _get_css_refs(self):
        """Adds files referenced in stylesheets and rewrite the URLs inside those stylesheets"""
        config = Config.getInstance()
        for path in self._css_files:
            src_path = os.path.join(config.getHtdocsDir(), path)
            dst_path = os.path.join(self._staticPath, path)
            if dst_path in self._downloaded_files and not os.path.exists(src_path):
                css = self._downloaded_files[dst_path]
            else:
                with open(src_path, 'rb') as f:
                    css = f.read()
            # Extract all paths inside url()
            urls = set(m.group('url') for m in RE_CSS_URL.finditer(css) if m.group('url')[0] != '#')
            for url in urls:
                orig_url = url
                url = _remove_qs(url)  # get rid of cache busters
                if url[0] == '/':
                    # make it relative and resolve '..' elements
                    url = os.path.normpath(url[1:])
                    # anything else is straightforward: the url is now relative to the htdocs folder
                    ref_src_path = os.path.join(config.getHtdocsDir(), url)
                    ref_dst_path = os.path.join(self._staticPath, url)
                    # the new url is relative to the css location
                    static_url = os.path.relpath(url, os.path.dirname(path))
                else:
                    # make the relative path absolute (note: it's most likely NOT relative to htdocs!)
                    css_abs_path = os.path.join(config.getHtdocsDir(), path)
                    # now we can combine the relative url with that path to get the proper paths of the resource
                    ref_src_path = os.path.normpath(os.path.join(os.path.dirname(css_abs_path), url))
                    ref_dst_path = os.path.normpath(os.path.join(self._staticPath, os.path.dirname(path), url))
                    static_url = os.path.relpath(ref_src_path, os.path.dirname(css_abs_path))
                if not os.path.isfile(ref_src_path):
                    htdocs_relative_path = os.path.relpath(ref_src_path, config.getHtdocsDir())
                    self._failed_paths.add(htdocs_relative_path)
                else:
                    self._addFileFromSrc(ref_dst_path, ref_src_path)
                css = css.replace(orig_url, static_url)
            self._fileHandler.addNewFile(dst_path, css)

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

    def _normalize_path(self, path):
        return secure_filename(remove_tags(path))

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
        self._addPdf(self._conf, urlHandlers.UHConfTimeTablePDF, TimeTablePlain,
                     conf=self._conf, aw=self._rh._aw, legacy=True)
        # Generate contributions in PDF
        self._addPdf(self._conf, urlHandlers.UHContributionListToPDF, ContribsToPDF, conf=self._conf,
                     contribs=self._conf.getContributionList())

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
        if link.getName() == 'abstractsBook':
            self._addPdf(self._conf, urlHandlers.UHConfAbstractBook, AbstractBook, conf=self._conf, aw=self._rh._aw)
        if link.getName() == 'programme':
            self._addPdf(self._conf, urlHandlers.UHConferenceProgramPDF, ProgrammeToPDF,
                         conf=self._conf, legacy=True)

    def _getInternalPage(self, link):
        page = link.getPage()
        html = WPStaticInternalPageDisplay(self._rh, self._conf, page).display()
        self._addPage(html, urlHandlers.UHInternalPageDisplay, target=page)

    def _addPage(self, html, rh, target, **params):
        fname = os.path.join(self._mainPath, str(rh.getStaticURL(target, **params)))
        html = self._get_static_files(html)
        self._fileHandler.addNewFile(fname, html)

    def _getContrib(self, contrib):
        html = WPStaticContributionDisplay(self._rh, contrib, 0).display()
        self._addPage(html, urlHandlers.UHContributionDisplay, target=contrib)
        self._addPdf(contrib, urlHandlers.UHContribToPDF, ContribToPDF, contrib=contrib)

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
        sessionContribfile = os.path.join(self._mainPath,
                                          'contribs-' + urlHandlers.UHSessionDisplay.getStaticURL(session))
        htmlContrib = self._get_static_files(htmlContrib)
        self._fileHandler.addNewFile(sessionContribfile, htmlContrib)
        self._addPdf(session, urlHandlers.UHConfTimeTablePDF, TimeTablePlain, conf=self._conf, aw=self._rh._aw,
                     showSessions=[session.getId()], legacy=True)

    def _addPdf(self, event, pdfUrlHandler, generatorClass,
                legacy=False, **generatorParams):
        """
        `legacy` specifies whether reportlab should be used instead of the
        new LaTeX generation mechanism
        """
        tz = timezoneUtils.DisplayTZ(self._rh._aw, self._conf).getDisplayTZ()
        filename = os.path.join(self._mainPath, pdfUrlHandler.getStaticURL(event))
        pdf = generatorClass(tz=tz, **generatorParams)

        if legacy:
            self._fileHandler.addNewFile(filename, pdf.getPDFBin())
        else:
            with open(pdf.generate()) as f:
                self._fileHandler.addNewFile(filename, f.read())
