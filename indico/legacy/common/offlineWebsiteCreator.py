# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import inspect
import itertools
import os
import posixpath
import re
from contextlib import contextmanager

import requests
from bs4 import BeautifulSoup
from flask import current_app, request
from flask.helpers import get_root_path
from werkzeug.utils import secure_filename

from indico.core.config import config
from indico.legacy.common.contribPacker import ZIPFileHandler
from indico.legacy.pdfinterface.conference import AbstractBook, ContribsToPDF, ContribToPDF, ProgrammeToPDF
from indico.legacy.webinterface.pages.static import (WPStaticAuthorList, WPStaticConferenceDisplay,
                                                     WPStaticConferenceProgram, WPStaticContributionDisplay,
                                                     WPStaticContributionList, WPStaticCustomPage,
                                                     WPStaticDisplayRegistrationParticipantList, WPStaticSessionDisplay,
                                                     WPStaticSimpleEventDisplay, WPStaticSpeakerList,
                                                     WPStaticSubcontributionDisplay, WPStaticTimetable)
from indico.modules.attachments.models.attachments import AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.events.contributions.controllers.display import (RHAuthorList, RHContributionAuthor,
                                                                     RHContributionDisplay, RHContributionList,
                                                                     RHSpeakerList, RHSubcontributionDisplay)
from indico.modules.events.contributions.util import get_contribution_ical_file
from indico.modules.events.layout.models.menu import MenuEntryType
from indico.modules.events.layout.util import menu_entries_for_event
from indico.modules.events.models.events import EventType
from indico.modules.events.registration.controllers.display import RHParticipantList
from indico.modules.events.sessions.controllers.display import RHDisplaySession
from indico.modules.events.sessions.util import get_session_ical_file, get_session_timetable_pdf
from indico.modules.events.timetable.controllers.display import RHTimetable
from indico.modules.events.timetable.util import get_timetable_offline_pdf_generator
from indico.modules.events.tracks.controllers import RHDisplayTracks
from indico.util.string import strip_tags
from indico.web.assets.util import get_asset_path
from indico.web.flask.util import url_for
from indico.web.rh import RH


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
    elif path.startswith(config.BASE_URL):
        path = path[len(config.BASE_URL):]
    path = path.lstrip('/')
    path = _remove_qs(path)
    return path


def _rule_for_endpoint(endpoint):
    return next((x for x in current_app.url_map.iter_rules(endpoint) if 'GET' in x.methods), None)


@contextmanager
def _override_request_endpoint(endpoint):
    rule = _rule_for_endpoint(endpoint)
    assert rule is not None
    old_rule = request.url_rule
    request.url_rule = rule
    try:
        yield
    finally:
        request.url_rule = old_rule


def create_static_site(rh, event):
    cls = OfflineEventCreator if event.type_ in (EventType.lecture, EventType.meeting) else ConferenceOfflineCreator
    return cls(rh, event).create()


class OfflineEventCreator(object):
    def __init__(self, rh, event):
        self._rh = rh
        self.event = event
        self._display_tz = self.event.display_tzinfo.zone
        self._html = ""
        self._fileHandler = None
        self._mainPath = ""
        self._staticPath = ""
        self._failed_paths = set()
        self._css_files = set()
        self._downloaded_files = {}
        self._htdocs_dir = os.path.join(get_root_path('indico'), 'htdocs')

    def create(self):
        self._fileHandler = ZIPFileHandler()

        # create the home page html
        self._create_home()

        # Create main and static folders
        self._mainPath = self._normalize_path(u'OfflineWebsite-{}'.format(self.event.title))
        self._fileHandler.addDir(self._mainPath)
        self._staticPath = os.path.join(self._mainPath, "static")
        self._fileHandler.addDir(self._staticPath)
        # Add i18n js
        self._addFolderFromSrc(os.path.join(self._staticPath, 'js', 'indico', 'i18n'),
                               os.path.join(self._htdocs_dir, 'js', 'indico', 'i18n'))
        # Mathjax plugins can't be discovered by parsing the HTML
        self._addFolderFromSrc(os.path.join(self._staticPath, 'js', 'lib', 'mathjax'),
                               os.path.join(self._htdocs_dir, 'js', 'lib', 'mathjax'))

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

        # Create overview.html file (main page for the event)
        conferenceDisplayPath = os.path.join(self._mainPath, 'overview.html')
        self._fileHandler.addNewFile(conferenceDisplayPath, self._html)

        # Creating index.html file
        self._fileHandler.addNewFile('index.html',
                                     '<meta http-equiv="Refresh" content="0; url=%s">' % conferenceDisplayPath)

        self._fileHandler.close()
        return self._fileHandler.getPath()

    def _static_url_to_path(self, url):
        match = re.match(r'^static/assets/(core|plugin-(?P<plugin>[^/]+)|theme-(?P<theme>[^/]+))/(?P<path>.+)$', url)
        if match is not None:
            path = os.path.join(config.ASSETS_DIR, get_asset_path(**match.groupdict()))
        else:
            path = os.path.join(self._htdocs_dir, url)
        return re.sub(r'#.*$', '', path)

    def _get_static_files(self, html):
        soup = BeautifulSoup(html, 'lxml')
        images = set(_fix_url_path(x['src']) for x in soup.select('img[src]'))
        images |= set(_fix_url_path(x['href']) for x in soup.select('link[rel="shortcut icon"]'))
        scripts = set(_fix_url_path(x['src']) for x in soup.select('script[src]'))
        styles = set(_fix_url_path(x['href']) for x in soup.select('link[rel="stylesheet"]'))
        for path in itertools.chain(images, scripts, styles):
            src_path = self._static_url_to_path(path)
            dst_path = os.path.join(self._staticPath, path)
            if path in styles:
                self._css_files.add(path)
            if not os.path.isfile(src_path):
                self._failed_paths.add(path)
            elif path not in styles:
                self._addFileFromSrc(dst_path, src_path)
        for image in soup.select('img[src]'):
            image['src'] = os.path.join('static', _fix_url_path(image['src']))
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
        for path in self._failed_paths:
            dst_path = os.path.join(self._staticPath, path)
            if not self._fileHandler.hasFile(dst_path):
                response = requests.get(os.path.join(config.BASE_URL, path), verify=False)
                self._downloaded_files[dst_path] = response.content
                self._fileHandler.addNewFile(dst_path, response.content)

    def _get_css_refs(self):
        """Adds files referenced in stylesheets and rewrite the URLs inside those stylesheets"""
        for path in self._css_files:
            src_path = self._static_url_to_path(path)
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
                    ref_src_path = os.path.join(self._htdocs_dir, url)
                    ref_dst_path = os.path.join(self._staticPath, url)
                    # the new url is relative to the css location
                    static_url = os.path.relpath(url, os.path.dirname(path))
                else:
                    # make the relative path absolute (note: it's most likely NOT relative to htdocs!)
                    css_abs_path = os.path.join(self._htdocs_dir, path)
                    # now we can combine the relative url with that path to get the proper paths of the resource
                    ref_src_path = os.path.normpath(os.path.join(os.path.dirname(css_abs_path), url))
                    ref_dst_path = os.path.normpath(os.path.join(self._staticPath, os.path.dirname(path), url))
                    static_url = os.path.relpath(ref_src_path, os.path.dirname(css_abs_path))
                if not os.path.isfile(ref_src_path):
                    htdocs_relative_path = os.path.relpath(ref_src_path, self._htdocs_dir)
                    htdocs_relative_path = re.sub(r'#.*$', '', htdocs_relative_path)
                    self._failed_paths.add(htdocs_relative_path)
                else:
                    self._addFileFromSrc(ref_dst_path, ref_src_path)
                css = css.replace(orig_url, static_url)
            self._fileHandler.addNewFile(dst_path, css)

    def _create_home(self):
        self._html = WPStaticSimpleEventDisplay(self._rh, self.event, self.event.theme).display()

    def _create_other_pages(self):
        pass

    def _normalize_path(self, path):
        return secure_filename(strip_tags(path))

    def _getAllMaterial(self):
        self._addMaterialFrom(self.event, "events/conference")
        for contrib in self.event.contributions:
            self._addMaterialFrom(contrib, "agenda/%s-contribution" % contrib.id)
            for sc in contrib.subcontributions:
                self._addMaterialFrom(sc, "agenda/%s-subcontribution" % sc.id)
        for session in self.event.sessions:
            self._addMaterialFrom(session, "agenda/%s-session" % session.id)

    def _addMaterialFrom(self, target, categoryPath):
        for folder in AttachmentFolder.get_for_linked_object(target, preload_event=True):
            for attachment in folder.attachments:
                if attachment.type == AttachmentType.file:
                    dst_path = posixpath.join(self._mainPath, "files", categoryPath,
                                              "{}-{}".format(attachment.id, attachment.file.filename))
                    with attachment.file.get_local_path() as file_path:
                        self._addFileFromSrc(dst_path, file_path)

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
                if root.startswith(srcPath):
                    dst_dirpath = os.path.join(dstPath, root[len(srcPath):].strip('/'))
                else:
                    dst_dirpath = dstPath
                dst_filepath = os.path.join(dst_dirpath, filename)
                self._fileHandler.addDir(dst_dirpath)
                if not self._fileHandler.hasFile(dst_filepath):
                    self._fileHandler.add(dst_filepath, src_filepath)


class ConferenceOfflineCreator(OfflineEventCreator):
    def __init__(self, rh, event):
        super(ConferenceOfflineCreator, self).__init__(rh, event)
        # Menu entries we want to include in the offline version.
        # Those which are backed by a WP class get their name from that class;
        # the others are simply hardcoded.
        self._menu_offline_items = {'overview': None, 'abstracts_book': None}
        rhs = {RHParticipantList: WPStaticDisplayRegistrationParticipantList,
               RHContributionList: WPStaticContributionList,
               RHAuthorList: WPStaticAuthorList,
               RHSpeakerList: WPStaticSpeakerList,
               RHTimetable: WPStaticTimetable,
               RHDisplayTracks: WPStaticConferenceProgram}
        for rh_cls, wp in rhs.iteritems():
            rh = rh_cls()
            rh.view_class = wp
            if rh_cls is RHTimetable:
                rh.view_class_simple = WPStaticSimpleEventDisplay
            self._menu_offline_items[wp.menu_entry_name] = rh

    def _create_home(self):
        p = WPStaticConferenceDisplay(self._rh, self.event)
        self._html = p.display()

    def _create_other_pages(self):
        # Getting all menu items
        self._get_menu_items()
        # Getting conference timetable in PDF
        self._addPdf(self.event, 'timetable.export_default_pdf',
                     get_timetable_offline_pdf_generator(self.event))
        # Generate contributions in PDF
        self._addPdf(self.event, 'contributions.contribution_list_pdf', ContribsToPDF, event=self.event,
                     contribs=self.event.contributions)

        # Getting specific pages for contributions
        for contrib in self.event.contributions:
            self._getContrib(contrib)
            # Getting specific pages for subcontributions
            for subcontrib in contrib.subcontributions:
                self._getSubContrib(subcontrib)

        for session in self.event.sessions:
            self._getSession(session)

    def _get_menu_items(self):
        entries = menu_entries_for_event(self.event)
        visible_entries = [e for e in itertools.chain(entries, *(e.children for e in entries)) if e.is_visible]
        for entry in visible_entries:
            if entry.type == MenuEntryType.page:
                self._get_custom_page(entry.page)
            elif entry.type == MenuEntryType.internal_link:
                self._get_builtin_page(entry)
            # we ignore plugin links as there is no way for plugins to
            # register something to be included in the static site

    def _get_builtin_page(self, entry):
        obj = self._menu_offline_items.get(entry.name)
        if isinstance(obj, RH):
            request.view_args = {'confId': self.event.id}
            with _override_request_endpoint(obj.view_class.endpoint):
                obj._process_args()
                self._addPage(obj._process(), obj.view_class.endpoint, self.event)
        if entry.name == 'abstracts_book':
            self._addPdf(self.event, 'abstracts.export_boa', AbstractBook, event=self.event)
        if entry.name == 'program':
            self._addPdf(self.event, 'tracks.program_pdf', ProgrammeToPDF, event=self.event)

    def _get_custom_page(self, page):
        html = WPStaticCustomPage.render_template('page.html', self.event, page=page)
        self._addPage(html, 'event_pages.page_display', page)

    def _getUrl(self, uh_or_endpoint, target, **params):
        if isinstance(uh_or_endpoint, basestring):
            return url_for(uh_or_endpoint, target, **params)
        else:
            return str(uh_or_endpoint.getStaticURL(target, **params))

    def _addPage(self, html, uh_or_endpoint, target=None, **params):
        url = self._getUrl(uh_or_endpoint, target, **params)
        fname = os.path.join(self._mainPath, url)
        html = self._get_static_files(html)
        self._fileHandler.addNewFile(fname, html)

    def _add_from_rh(self, rh_class, view_class, params, url_for_target):
        rh = rh_class()
        rh.view_class = view_class
        request.view_args = params
        with _override_request_endpoint(rh.view_class.endpoint):
            rh._process_args()
            html = rh._process()
        self._addPage(html, rh.view_class.endpoint, url_for_target)

    def _getContrib(self, contrib):
        self._add_from_rh(RHContributionDisplay, WPStaticContributionDisplay,
                          {'confId': self.event.id, 'contrib_id': contrib.id},
                          contrib)
        self._addPdf(contrib, 'contributions.export_pdf', ContribToPDF, contrib=contrib)

        for author in contrib.primary_authors:
            self._getAuthor(contrib, author)
        for author in contrib.secondary_authors:
            self._getAuthor(contrib, author)

        if contrib.timetable_entry:
            self._add_file(get_contribution_ical_file(contrib), 'contributions.export_ics', contrib)

    def _getSubContrib(self, subcontrib):
        self._add_from_rh(RHSubcontributionDisplay, WPStaticSubcontributionDisplay,
                          {'confId': self.event.id, 'contrib_id': subcontrib.contribution.id,
                           'subcontrib_id': subcontrib.id}, subcontrib)

    def _getAuthor(self, contrib, author):
        rh = RHContributionAuthor()
        params = {'confId': self.event.id, 'contrib_id': contrib.id, 'person_id': author.id}
        request.view_args = params
        with _override_request_endpoint('contributions.display_author'):
            rh._process_args()
            html = rh._process()
        self._addPage(html, 'contributions.display_author', self.event, contrib_id=contrib.id, person_id=author.id)

    def _getSession(self, session):
        self._add_from_rh(RHDisplaySession, WPStaticSessionDisplay,
                          {'confId': self.event.id, 'session_id': session.id}, session)

        pdf = get_session_timetable_pdf(session, tz=self._display_tz)
        self._addPdf(session, 'sessions.export_session_timetable', pdf)

        self._add_file(get_session_ical_file(session), 'sessions.export_ics', session)

    def _addPdf(self, target, uh_or_endpoint, generator_class_or_instance, **generatorParams):
        if inspect.isclass(generator_class_or_instance):
            pdf = generator_class_or_instance(tz=self._display_tz, **generatorParams)
        else:
            pdf = generator_class_or_instance

        if hasattr(pdf, 'getPDFBin'):
            # Got legacy reportlab PDF generator instead of the LaTex-based one
            self._add_file(pdf.getPDFBin(), uh_or_endpoint, target)
        else:
            with open(pdf.generate()) as f:
                self._add_file(f, uh_or_endpoint, target)

    def _add_file(self, file_like_or_str, uh_or_endpoint, target):
        if isinstance(file_like_or_str, str):
            content = file_like_or_str
        else:
            # FIXME: the FileHandler should accept a file-like object
            content = file_like_or_str.read()
        filename = os.path.join(self._mainPath, self._getUrl(uh_or_endpoint, target))
        self._fileHandler.addNewFile(filename, content)
