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

from io import BytesIO
import mimetypes

from flask import flash, redirect, request, jsonify
from werkzeug.exceptions import NotFound

from indico.modules.events.layout import layout_settings
from indico.modules.events.layout.forms import LayoutForm, MenuEntryForm, MenuLinkForm, MenuPageForm
from indico.modules.events.layout.models.menu import MenuEntry
from indico.modules.events.layout.util import menu_entries_for_event, move_entry, get_event_logo
from indico.modules.events.layout.views import WPLayoutEdit, WPMenuEdit
from indico.modules.events.models.events import Event
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import redirect_or_jsonify, url_for, send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_template
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


def _render_menu_entry(entry):
    tpl = get_template_module('events/layout/_menu.html')
    return tpl.menu_entry(entry=entry)


class RHLayoutLogoUpload(RHConferenceModifBase):
    CSRF_ENABLED = True

    def _process(self):
        event = Event.find(Event.id == self._conf.getId()).one()
        f = request.files.get('file')
        content = f.read()
        event.logo = content
        content_type = mimetypes.guess_type(f.filename)[0] or f.mimetype or 'application/octet-stream'
        event.logo_metadata = {
            'size': len(content),
            'file_name': f.filename,
            'content_type': content_type
        }
        return jsonify({'success': True})


class RHLogoDisplay(RHConferenceBaseDisplay):
    def _process(self):
        logo_data = get_event_logo(self._conf)
        logo_content = BytesIO(logo_data['content'])
        metadata = logo_data['metadata']
        return send_file(metadata['file_name'], logo_content, mimetype=metadata['content_type'], no_cache=True,
                         conditional=True)


class RHLayoutEdit(RHConferenceModifBase):
    def _process(self):
        defaults = FormDefaults(**layout_settings.get_all(self._conf))
        event = Event.find(Event.id == self._conf.getId()).one()
        form = LayoutForm(event=event, obj=defaults)
        if form.validate_on_submit():
            layout_settings.set_multi(self._conf, {
                'is_searchable': form.data['is_searchable'],
                'show_nav_bar': form.data['show_nav_bar'],
                'show_social_badges': form.data['show_social_badges'],
                'show_banner': form.data['show_banner'],
                'header_text_color': form.data['header_text_color'],
                'header_background_color': form.data['header_background_color'],
                'announcement': form.data['announcement'],
                'show_announcement': form.data['show_announcement']
                })
            flash(_('Settings saved'), 'success')
            return redirect(url_for('event_layout.index', self._conf))
        else:
            if event.logo:
                form.logo.data = {
                    'url': url_for('event_images.logo-display', self._conf),
                    'file_name': event.logo_metadata['file_name'],
                    'size': event.logo_metadata['size'],
                    'content_type': event.logo_metadata['content_type']
                }
        return WPLayoutEdit.render_template('layout.html', self._conf, form=form, event=self._conf)


class RHMenuEdit(RHConferenceModifBase):
    def _process(self):
        return WPMenuEdit.render_template('menu_edit.html', self._conf,
                                          menu=menu_entries_for_event(self._conf, show_hidden=True))


class RHMenuEntryEditBase(RHConferenceModifBase):
    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.entry = MenuEntry.find_first(id=request.view_args['menu_entry_id'], event_id=self._conf.getId())
        if not self.entry:
            raise NotFound


class RHMenuEntryEdit(RHMenuEntryEditBase):
    def _process(self):
        defaults = FormDefaults(self.entry)
        form_cls = MenuEntryForm
        if self.entry.is_user_link:
            form_cls = MenuLinkForm
        elif self.entry.is_page:
            form_cls = MenuPageForm
        form = form_cls(linked_object=self.entry, obj=defaults)
        if form.validate_on_submit():
            form.populate_obj(self.entry)
            return redirect_or_jsonify(url_for('.menu', self._conf), entry=_render_menu_entry(self.entry))
        return jsonify_template('events/layout/menu_entry_form.html', form=form)


class RHMenuEntryPosition(RHMenuEntryEditBase):
    def _process(self):
        position = request.form.get('position')
        try:
            position = int(position)
        except ValueError:
            if position:
                jsonify_data(success=False)
            position = None
        move_entry(self.entry, position)
        return jsonify_data()


class RHMenuEntryVisibility(RHMenuEntryEditBase):
    def _process(self):
        self.entry.visible = not self.entry.visible
        return redirect_or_jsonify(url_for('.menu', self._conf), visible=self.entry.visible)
