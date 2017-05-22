# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

import os
from io import BytesIO

from flask import flash, redirect, request, session
from PIL import Image
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.legacy.webinterface.pages.conferences import WPConferenceDisplay
from indico.legacy.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from indico.modules.events.layout import layout_settings, logger
from indico.modules.events.layout.forms import (ConferenceLayoutForm, CSSForm, CSSSelectionForm,
                                                LectureMeetingLayoutForm, LogoForm)
from indico.modules.events.layout.util import get_css_file_data, get_css_url, get_logo_data
from indico.modules.events.layout.views import WPLayoutEdit
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.models.events import EventType
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.util.string import crc32, to_unicode
from indico.web.flask.util import send_file, url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data


class RHLayoutBase(RHManageEventBase):
    pass


class RHLayoutEdit(RHLayoutBase):
    def _process(self):
        if self.event_new.type_ == EventType.conference:
            return self._process_conference()
        else:
            return self._process_lecture_meeting()

    def _get_form_defaults(self):
        defaults = FormDefaults(**layout_settings.get_all(self.event_new))
        defaults.timetable_theme = self.event_new.theme
        return defaults

    def _process_lecture_meeting(self):
        form = LectureMeetingLayoutForm(obj=self._get_form_defaults(), event=self.event_new)
        if form.validate_on_submit():
            layout_settings.set_multi(self.event_new, form.data)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.index', self.event_new))
        return WPLayoutEdit.render_template('layout_meeting_lecture.html', self._conf, form=form, event=self.event_new)

    def _process_conference(self):
        form = ConferenceLayoutForm(obj=self._get_form_defaults(), event=self.event_new)
        css_form = CSSForm()
        logo_form = LogoForm()

        if form.validate_on_submit():
            data = {unicode(key): value for key, value in form.data.iteritems() if key in layout_settings.defaults}
            layout_settings.set_multi(self.event_new, data)
            if form.theme.data == '_custom':
                layout_settings.set(self.event_new, 'use_custom_css', True)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.index', self.event_new))
        else:
            if self.event_new.logo_metadata:
                logo_form.logo.data = self.event_new
            if self.event_new.has_stylesheet:
                css_form.css_file.data = self.event_new
        return WPLayoutEdit.render_template('layout_conference.html', self._conf, form=form, event=self.event_new,
                                            logo_form=logo_form, css_form=css_form)


class RHLayoutLogoUpload(RHLayoutBase):
    def _process(self):
        f = request.files['logo']
        try:
            img = Image.open(f)
        except IOError:
            flash(_('You cannot upload this file as a logo.'), 'error')
            return jsonify_data(content=None)
        if img.format.lower() not in {'jpeg', 'png', 'gif'}:
            flash(_('The file has an invalid format ({format})').format(format=img.format), 'error')
            return jsonify_data(content=None)
        if img.mode == 'CMYK':
            flash(_('The logo you uploaded is using the CMYK colorspace and has been converted to RGB. Please check if '
                    'the colors are correct and convert it manually if necessary.'), 'warning')
            img = img.convert('RGB')
        image_bytes = BytesIO()
        img.save(image_bytes, 'PNG')
        image_bytes.seek(0)
        content = image_bytes.read()
        self.event_new.logo = content
        self.event_new.logo_metadata = {
            'hash': crc32(content),
            'size': len(content),
            'filename': os.path.splitext(secure_filename(f.filename, 'logo'))[0] + '.png',
            'content_type': 'image/png'
        }
        flash(_('New logo saved'), 'success')
        logger.info("New logo '%s' uploaded by %s (%s)", f.filename, session.user, self.event_new)
        return jsonify_data(content=get_logo_data(self.event_new))


class RHLayoutLogoDelete(RHLayoutBase):
    def _process(self):
        self.event_new.logo = None
        self.event_new.logo_metadata = None
        flash(_('Logo deleted'), 'success')
        logger.info("Logo of %s deleted by %s", self.event_new, session.user)
        return jsonify_data(content=None)


class RHLayoutCSSUpload(RHLayoutBase):
    def _process(self):
        f = request.files['css_file']
        self.event_new.stylesheet = to_unicode(f.read()).strip()
        self.event_new.stylesheet_metadata = {
            'hash': crc32(self.event_new.stylesheet),
            'size': len(self.event_new.stylesheet),
            'filename': secure_filename(f.filename, 'stylesheet.css')
        }
        db.session.flush()
        flash(_('New CSS file saved. Do not forget to enable it ("Use custom CSS") after verifying that it is correct '
                'using the preview.'), 'success')
        logger.info('CSS file for %s uploaded by %s', self.event_new, session.user)
        return jsonify_data(content=get_css_file_data(self.event_new))


class RHLayoutCSSDelete(RHLayoutBase):

    def _process(self):
        self.event_new.stylesheet = None
        self.event_new.stylesheet_metadata = None
        layout_settings.set(self.event_new, 'use_custom_css', False)
        flash(_('CSS file deleted'), 'success')
        logger.info("CSS file for %s deleted by %s", self.event_new, session.user)
        return jsonify_data(content=None)


class RHLayoutCSSPreview(RHLayoutBase):
    def _process(self):
        form = CSSSelectionForm(event=self.event_new, formdata=request.args, csrf_enabled=False)
        css_url = None
        if form.validate():
            css_url = get_css_url(self.event_new, force_theme=form.theme.data, for_preview=True)
        return WPConferenceDisplay(self, self._conf, css_override_form=form, css_url_override=css_url).display()


class RHLayoutCSSSaveTheme(RHLayoutBase):
    def _process(self):
        form = CSSSelectionForm(event=self.event_new)
        if form.validate_on_submit():
            layout_settings.set(self.event_new, 'use_custom_css', form.theme.data == '_custom')
            if form.theme.data != '_custom':
                layout_settings.set(self._conf, 'theme', form.theme.data)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.index', self.event_new))


class RHLogoDisplay(RHConferenceBaseDisplay):
    def _process(self):
        if not self.event_new.has_logo:
            raise NotFound
        metadata = self.event_new.logo_metadata
        return send_file(metadata['filename'], BytesIO(self.event_new.logo), mimetype=metadata['content_type'],
                         conditional=True)


class RHLayoutCSSDisplay(RHConferenceBaseDisplay):
    def _process(self):
        if not self.event_new.has_stylesheet:
            raise NotFound
        data = BytesIO(self.event_new.stylesheet.encode('utf-8'))
        return send_file(self.event_new.stylesheet_metadata['filename'], data, mimetype='text/css', conditional=True)
