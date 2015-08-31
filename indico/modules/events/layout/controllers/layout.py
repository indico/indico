# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import binascii
import os
from io import BytesIO

from flask import flash, redirect, request, session
from indico.util.string import to_unicode
from PIL import Image
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.modules.events.layout import layout_settings, logger
from indico.modules.events.layout.forms import (LayoutForm, LogoForm, CSSForm, CSSSelectionForm)
from indico.modules.events.layout.util import get_css_url
from indico.modules.events.layout.views import WPLayoutEdit
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.web.flask.util import url_for, send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data
from MaKaC.webinterface.pages.conferences import WPConfModifPreviewCSS
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


def _logo_data(event):
    return {
        'url': event.logo_url,
        'filename': event.logo_metadata['filename'],
        'size': event.logo_metadata['size'],
        'content_type': event.logo_metadata['content_type']
    }


def _css_file_data(event):
    return {
        'filename': event.stylesheet_metadata['filename'],
        'size': event.stylesheet_metadata['size'],
        'content_type': 'text/css'
    }


class RHLayoutBase(RHConferenceModifBase):
    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.event = self._conf.as_event


class RHLayoutEdit(RHLayoutBase):
    def _checkProtection(self):
        RHLayoutBase._checkProtection(self)
        if self._conf.getType() != 'conference':
            raise NotFound('Only conferences have layout settings')

    def _process(self):
        defaults = FormDefaults(**layout_settings.get_all(self._conf))
        form = LayoutForm(obj=defaults, event=self.event)
        css_form = CSSForm()
        logo_form = LogoForm()

        if form.validate_on_submit():
            data = {unicode(key): value for key, value in form.data.iteritems() if key in layout_settings.defaults}
            layout_settings.set_multi(self._conf, data)
            if form.theme.data == '_custom':
                layout_settings.set(self._conf, 'use_custom_css', True)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('event_layout.index', self._conf))
        else:
            if self.event.logo_metadata:
                logo_form.logo.data = _logo_data(self.event)
            if self.event.has_stylesheet:
                css_form.css_file.data = _css_file_data(self.event)
        return WPLayoutEdit.render_template('layout.html', self._conf, form=form, event=self._conf,
                                            logo_form=logo_form, css_form=css_form)


class RHLayoutLogoUpload(RHLayoutBase):
    def _process(self):
        f = request.files['file']
        try:
            img = Image.open(f)
        except IOError:
            flash(_('You cannot upload this file as a logo.'), 'error')
            return jsonify_data(content={})
        if img.format.lower() not in {'jpeg', 'png', 'gif'}:
            flash(_('The file has an invalid format ({format})').format(format=img.format), 'error')
            return jsonify_data(content={})
        image_bytes = BytesIO()
        img.save(image_bytes, 'PNG')
        image_bytes.seek(0)
        content = image_bytes.read()
        self.event.logo = content
        self.event.logo_metadata = {
            'hash': binascii.crc32(content) & 0xffffffff,
            'size': len(content),
            'filename': os.path.splitext(secure_filename(f.filename, 'logo'))[0] + '.png',
            'content_type': 'image/png'
        }
        flash(_('New logo saved'), 'success')
        logger.info("New logo '{}' uploaded by {} ({})".format(f.filename, session.user, self.event))
        return jsonify_data(content=_logo_data(self.event))


class RHLayoutLogoDelete(RHLayoutBase):
    def _process(self):
        self.event.logo = None
        self.event.logo_metadata = None
        flash(_('Logo deleted'), 'success')
        logger.info("Logo of {} deleted by {}".format(self.event, session.user))
        return jsonify_data(content=None)


class RHLayoutCSSUpload(RHLayoutBase):
    def _process(self):
        f = request.files['file']
        self.event.stylesheet = to_unicode(f.read()).strip()
        self.event.stylesheet_metadata = {
            'hash': binascii.crc32(self.event.stylesheet) & 0xffffffff,
            'size': len(self.event.stylesheet),
            'filename': secure_filename(f.filename, 'stylesheet.css')
        }
        db.session.flush()
        flash(_('New CSS file saved. Do not forget to enable it ("Use custom CSS") after verifying that it is correct '
                'using the preview.'), 'success')
        logger.info('CSS file for {} uploaded by {}'.format(self.event, session.user))
        return jsonify_data(content=_css_file_data(self.event))


class RHLayoutCSSDelete(RHLayoutBase):

    def _process(self):
        self.event.stylesheet = None
        self.event.stylesheet_metadata = None
        layout_settings.set(self.event, 'use_custom_css', False)
        flash(_('CSS file deleted'), 'success')
        logger.info("CSS file for {} deleted by {}".format(self.event, session.user))
        return jsonify_data(content=None)


class RHLayoutCSSPreview(RHLayoutBase):
    def _process(self):
        form = CSSSelectionForm(event=self.event, formdata=request.args, csrf_enabled=False)
        css_url = None
        if form.validate():
            css_url = get_css_url(self.event, force_theme=form.theme.data, for_preview=True)
        return WPConfModifPreviewCSS(self, self._conf, form=form, css_url=css_url).display()


class RHLayoutCSSSaveTheme(RHLayoutBase):
    def _process(self):
        form = CSSSelectionForm(event=self.event)
        if form.validate_on_submit():
            layout_settings.set(self.event, 'use_custom_css', form.theme.data == '_custom')
            if form.theme.data != '_custom':
                layout_settings.set(self._conf, 'theme', form.theme.data)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('event_layout.index', self.event))


class RHLogoDisplay(RHConferenceBaseDisplay):
    def _process(self):
        event = self._conf.as_event
        if not event.has_logo:
            raise NotFound
        metadata = event.logo_metadata
        return send_file(metadata['filename'], BytesIO(event.logo), mimetype=metadata['content_type'], conditional=True)


class RHLayoutCSSDisplay(RHConferenceBaseDisplay):
    def _process(self):
        event = self._conf.as_event
        if not event.has_stylesheet:
            raise NotFound
        data = BytesIO(event.stylesheet.encode('utf-8'))
        return send_file(event.stylesheet_metadata['filename'], data, mimetype='text/css', conditional=True)
