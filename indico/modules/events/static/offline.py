# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import inspect
import itertools
import os
import posixpath
import re
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from flask import g, request, session
from flask.helpers import get_root_path
from werkzeug.utils import secure_filename

from indico.core.config import config
from indico.core.plugins import plugin_engine
from indico.legacy.pdfinterface.conference import ProgrammeToPDF
from indico.legacy.pdfinterface.latex import AbstractBook, ContribsToPDF, ContribToPDF
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
from indico.modules.events.static.util import collect_static_files, override_request_endpoint, rewrite_css_urls
from indico.modules.events.timetable.controllers.display import RHTimetable
from indico.modules.events.timetable.util import get_timetable_offline_pdf_generator
from indico.modules.events.tracks.controllers import RHDisplayTracks
from indico.util.fs import chmod_umask
from indico.util.string import strip_tags
from indico.web.assets.vars_js import generate_global_file, generate_i18n_file, generate_user_file
from indico.web.flask.util import url_for
from indico.web.rh import RH


def create_static_site(rh, event):
    """Create a static (offline) version of an Indico event.

    :param rh: Request handler object
    :param event: Event in question
    :return: Path to the resulting ZIP file
    """
    try:
        g.static_site = True
        g.rh = rh
        cls = StaticEventCreator if event.type_ in (EventType.lecture, EventType.meeting) else StaticConferenceCreator
        return cls(rh, event).create()
    finally:
        g.static_site = False
        g.rh = None


def _normalize_path(path):
    return secure_filename(strip_tags(path))


class StaticEventCreator(object):
    """Define process which generates a static (offline) version of an Indico event."""

    def __init__(self, rh, event):
        self._rh = rh
        self.event = event
        self._display_tz = self.event.display_tzinfo.zone
        self._zip_file = None
        self._content_dir = _normalize_path(u'OfflineWebsite-{}'.format(event.title))
        self._web_dir = os.path.join(get_root_path('indico'), 'web')
        self._static_dir = os.path.join(self._web_dir, 'static')

    def create(self):
        """Trigger the creation of a ZIP file containing the site."""
        temp_file = NamedTemporaryFile(suffix='indico.tmp', dir=config.TEMP_DIR)
        self._zip_file = ZipFile(temp_file.name, 'w', allowZip64=True)

        with collect_static_files() as used_assets:
            # create the home page html
            html = self._create_home().encode('utf-8')

            # Mathjax plugins can only be known in runtime
            self._copy_folder(os.path.join(self._content_dir, 'static', 'dist', 'js', 'mathjax'),
                              os.path.join(self._static_dir, 'dist', 'js', 'mathjax'))

            # Materials and additional pages
            self._copy_all_material()
            self._create_other_pages()

            # Create index.html file (main page for the event)
            index_path = os.path.join(self._content_dir, 'index.html')
            self._zip_file.writestr(index_path, html)

            self._write_generated_js()

        # Copy static assets to ZIP file
        self._copy_static_files(used_assets)
        self._copy_plugin_files(used_assets)
        if config.CUSTOMIZATION_DIR:
            self._copy_customization_files(used_assets)

        temp_file.delete = False
        chmod_umask(temp_file.name)
        self._zip_file.close()
        return temp_file.name

    def _write_generated_js(self):
        global_js = generate_global_file().encode('utf-8')
        user_js = generate_user_file().encode('utf-8')
        i18n_js = u"window.TRANSLATIONS = {};".format(generate_i18n_file(session.lang)).encode('utf-8')
        react_i18n_js = u"window.REACT_TRANSLATIONS = {};".format(
            generate_i18n_file(session.lang, react=True)).encode('utf-8')
        gen_path = os.path.join(self._content_dir, 'assets')
        self._zip_file.writestr(os.path.join(gen_path, 'js-vars', 'global.js'), global_js)
        self._zip_file.writestr(os.path.join(gen_path, 'js-vars', 'user.js'), user_js)
        self._zip_file.writestr(os.path.join(gen_path, 'i18n', session.lang + '.js'), i18n_js)
        self._zip_file.writestr(os.path.join(gen_path, 'i18n', session.lang + '-react.js'), react_i18n_js)

    def _copy_static_files(self, used_assets):
        # add favicon
        used_assets.add('static/images/indico.ico')
        # assets
        css_files = {url for url in used_assets if re.match(r'static/dist/.*\.css$', url)}
        for file_path in css_files:
            with open(os.path.join(self._web_dir, file_path)) as f:
                rewritten_css, used_urls, __ = rewrite_css_urls(self.event, f.read())
                used_assets |= used_urls
                self._zip_file.writestr(os.path.join(self._content_dir, file_path), rewritten_css)
        for file_path in used_assets - css_files:
            if not re.match('^static/(images|fonts|dist)/(?!js/ckeditor/)', file_path):
                continue
            self._copy_file(os.path.join(self._content_dir, file_path),
                            os.path.join(self._web_dir, file_path))

    def _copy_plugin_files(self, used_assets):
        css_files = {url for url in used_assets if re.match(r'static/plugins/.*\.css$', url)}
        for file_path in css_files:
            plugin_name, path = re.match(r'static/plugins/([^/]+)/(.+.css)', file_path).groups()
            plugin = plugin_engine.get_plugin(plugin_name)
            with open(os.path.join(plugin.root_path, 'static', path)) as f:
                rewritten_css, used_urls, __ = rewrite_css_urls(self.event, f.read())
                used_assets |= used_urls
                self._zip_file.writestr(os.path.join(self._content_dir, file_path), rewritten_css)
        for file_path in used_assets - css_files:
            match = re.match(r'static/plugins/([^/]+)/(.+)', file_path)
            if not match:
                continue
            plugin_name, path = match.groups()
            plugin = plugin_engine.get_plugin(plugin_name)
            self._copy_file(os.path.join(self._content_dir, file_path),
                            os.path.join(plugin.root_path, 'static', path))

    def _strip_custom_prefix(self, url):
        # strip the 'static/custom/' prefix from the given url/path
        return '/'.join(url.split('/')[2:])

    def _copy_customization_files(self, used_assets):
        css_files = {url for url in used_assets if re.match(r'static/custom/.*\.css$', url)}
        for file_path in css_files:
            with open(os.path.join(config.CUSTOMIZATION_DIR, self._strip_custom_prefix(file_path))) as f:
                rewritten_css, used_urls, __ = rewrite_css_urls(self.event, f.read())
                used_assets |= used_urls
                self._zip_file.writestr(os.path.join(self._content_dir, file_path), rewritten_css)
        for file_path in used_assets - css_files:
            if not file_path.startswith('static/custom/'):
                continue
            self._copy_file(os.path.join(self._content_dir, file_path),
                            os.path.join(config.CUSTOMIZATION_DIR, self._strip_custom_prefix(file_path)))

    def _create_home(self):
        return WPStaticSimpleEventDisplay(self._rh, self.event, self.event.theme).display()

    def _create_other_pages(self):
        pass

    def _copy_all_material(self):
        self._add_material(self.event, '')
        for contrib in self.event.contributions:
            if not contrib.can_access(None):
                continue
            self._add_material(contrib, "%s-contribution" % contrib.friendly_id)
            for sc in contrib.subcontributions:
                self._add_material(sc, "%s-subcontribution" % sc.friendly_id)
        for session_ in self.event.sessions:
            if not session_.can_access(None):
                continue
            self._add_material(session_, "%s-session" % session_.friendly_id)

    def _add_material(self, target, type_):
        for folder in AttachmentFolder.get_for_linked_object(target, preload_event=True):
            for attachment in folder.attachments:
                if not attachment.can_access(None):
                    continue
                if attachment.type == AttachmentType.file:
                    dst_path = posixpath.join(self._content_dir, "material", type_,
                                              "{}-{}".format(attachment.id, attachment.file.filename))
                    with attachment.file.get_local_path() as file_path:
                        self._copy_file(dst_path, file_path)

    def _copy_file(self, dest, src):
        """Copy a file from a source path to a destination inside the ZIP."""
        self._zip_file.write(src, dest)

    def _copy_folder(self, dest, src):
        for root, subfolders, files in os.walk(src):
            dst_dirpath = os.path.join(dest, os.path.relpath(root, src))
            for filename in files:
                src_filepath = os.path.join(src, root, filename)
                self._zip_file.write(src_filepath, os.path.join(dst_dirpath, filename))


class StaticConferenceCreator(StaticEventCreator):
    def __init__(self, rh, event):
        super(StaticConferenceCreator, self).__init__(rh, event)
        # Menu entries we want to include in the offline version.
        # Those which are backed by a WP class get their name from that class;
        # the others are simply hardcoded.
        self._menu_offline_items = {
            'overview': None,
            'abstracts_book': None
        }
        rhs = {
            RHParticipantList: WPStaticDisplayRegistrationParticipantList,
            RHContributionList: WPStaticContributionList,
            RHAuthorList: WPStaticAuthorList,
            RHSpeakerList: WPStaticSpeakerList,
            RHTimetable: WPStaticTimetable,
            RHDisplayTracks: WPStaticConferenceProgram
        }
        for rh_cls, wp in rhs.viewitems():
            rh = rh_cls()
            rh.view_class = wp
            if rh_cls is RHTimetable:
                rh.view_class_simple = WPStaticSimpleEventDisplay
            self._menu_offline_items[wp.menu_entry_name] = rh

    def _create_home(self):
        if self.event.has_stylesheet:
            css, used_urls, used_images = rewrite_css_urls(self.event, self.event.stylesheet)
            g.used_url_for_assets |= used_urls
            self._zip_file.writestr(os.path.join(self._content_dir, 'custom.css'), css)
            for image_file in used_images:
                with image_file.open() as f:
                    self._zip_file.writestr(os.path.join(self._content_dir,
                                                         'images/{}-{}'.format(image_file.id, image_file.filename)),
                                            f.read())
        if self.event.has_logo:
            self._zip_file.writestr(os.path.join(self._content_dir, 'logo.png'), self.event.logo)
        return WPStaticConferenceDisplay(self._rh, self.event).display()

    def _create_other_pages(self):
        # Getting all menu items
        self._get_menu_items()
        # Getting conference timetable in PDF
        self._add_pdf(self.event, 'timetable.export_default_pdf',
                      get_timetable_offline_pdf_generator(self.event))
        if config.LATEX_ENABLED:
            # Generate contributions in PDF
            self._add_pdf(self.event, 'contributions.contribution_list_pdf', ContribsToPDF, event=self.event,
                          contribs=[c for c in self.event.contributions if c.can_access(None)])

        # Getting specific pages for contributions
        for contrib in self.event.contributions:
            if not contrib.can_access(None):
                continue
            self._get_contrib(contrib)
            # Getting specific pages for subcontributions
            for subcontrib in contrib.subcontributions:
                self._get_sub_contrib(subcontrib)

        for session_ in self.event.sessions:
            if not session_.can_access(None):
                continue
            self._get_session(session_)

    def _get_menu_items(self):
        entries = menu_entries_for_event(self.event)
        visible_entries = [e for e in itertools.chain(entries, *(e.children for e in entries)) if e.is_visible]
        for entry in visible_entries:
            if entry.type == MenuEntryType.page:
                self._get_custom_page(entry.page)
            elif entry.type == MenuEntryType.internal_link:
                self._get_builtin_page(entry)

    def _get_builtin_page(self, entry):
        obj = self._menu_offline_items.get(entry.name)
        if isinstance(obj, RH):
            request.view_args = {'confId': self.event.id}
            with override_request_endpoint(obj.view_class.endpoint):
                obj._process_args()
                self._add_page(obj._process(), obj.view_class.endpoint, self.event)
        if entry.name == 'abstracts_book' and config.LATEX_ENABLED:
            self._add_pdf(self.event, 'abstracts.export_boa', AbstractBook, event=self.event)
        if entry.name == 'program':
            self._add_pdf(self.event, 'tracks.program_pdf', ProgrammeToPDF, event=self.event)

    def _get_custom_page(self, page):
        html = WPStaticCustomPage.render_template('page.html', self.event, page=page)
        self._add_page(html, 'event_pages.page_display', page)

    def _get_url(self, uh_or_endpoint, target, **params):
        if isinstance(uh_or_endpoint, basestring):
            return url_for(uh_or_endpoint, target, **params)
        else:
            return str(uh_or_endpoint.getStaticURL(target, **params))

    def _add_page(self, html, uh_or_endpoint, target=None, **params):
        url = self._get_url(uh_or_endpoint, target, **params)
        fname = os.path.join(self._content_dir, url)
        self._zip_file.writestr(fname, html.encode('utf-8'))

    def _add_from_rh(self, rh_class, view_class, params, url_for_target):
        rh = rh_class()
        rh.view_class = view_class
        request.view_args = params
        with override_request_endpoint(rh.view_class.endpoint):
            rh._process_args()
            html = rh._process()
        self._add_page(html, rh.view_class.endpoint, url_for_target)

    def _get_contrib(self, contrib):
        self._add_from_rh(RHContributionDisplay, WPStaticContributionDisplay,
                          {'confId': self.event.id, 'contrib_id': contrib.id},
                          contrib)
        if config.LATEX_ENABLED:
            self._add_pdf(contrib, 'contributions.export_pdf', ContribToPDF, contrib=contrib)

        for author in contrib.primary_authors:
            self._get_author(contrib, author)
        for author in contrib.secondary_authors:
            self._get_author(contrib, author)

        if contrib.timetable_entry:
            self._add_file(get_contribution_ical_file(contrib), 'contributions.export_ics', contrib)

    def _get_sub_contrib(self, subcontrib):
        self._add_from_rh(RHSubcontributionDisplay, WPStaticSubcontributionDisplay,
                          {'confId': self.event.id, 'contrib_id': subcontrib.contribution.id,
                           'subcontrib_id': subcontrib.id}, subcontrib)

    def _get_author(self, contrib, author):
        rh = RHContributionAuthor()
        params = {'confId': self.event.id, 'contrib_id': contrib.id, 'person_id': author.id}
        request.view_args = params
        with override_request_endpoint('contributions.display_author'):
            rh._process_args()
            html = rh._process()
        self._add_page(html, 'contributions.display_author', self.event, contrib_id=contrib.id, person_id=author.id)

    def _get_session(self, session):
        self._add_from_rh(RHDisplaySession, WPStaticSessionDisplay,
                          {'confId': self.event.id, 'session_id': session.id}, session)

        pdf = get_session_timetable_pdf(session, tz=self._display_tz)
        self._add_pdf(session, 'sessions.export_session_timetable', pdf)

        self._add_file(get_session_ical_file(session), 'sessions.export_ics', session)

    def _add_pdf(self, target, uh_or_endpoint, generator_class_or_instance, **kwargs):
        if inspect.isclass(generator_class_or_instance):
            pdf = generator_class_or_instance(tz=self._display_tz, **kwargs)
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
            content = file_like_or_str.read()
        filename = os.path.join(self._content_dir, self._get_url(uh_or_endpoint, target))
        self._zip_file.writestr(filename, content)
