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

from flask import request
from werkzeug.exceptions import NotFound

from indico.modules.events.layout import layout_settings
from indico.modules.events.layout.forms import LayoutForm, MenuEntryForm, MenuLinkForm, MenuPageForm
from indico.modules.events.layout.models.menu import MenuEntry
from indico.modules.events.layout.util import menu_entries_for_event
from indico.modules.events.layout.views import WPLayoutEdit, WPMenuEdit
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import redirect_or_jsonify, url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_template
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


def _render_menu_entry(entry):
    tpl = get_template_module('events/layout/_menu.html')
    return tpl.menu_entry(entry=entry)


class RHLayoutEdit(RHConferenceModifBase):
    def _process(self):
        defaults = FormDefaults(**layout_settings.get_all(self._conf))
        form = LayoutForm(obj=defaults)
        if form.validate_on_submit():
            pass
        return WPLayoutEdit.render_template('layout.html', self._conf, form=form)


class RHMenuEdit(RHConferenceModifBase):
    def _process(self):
        return WPMenuEdit.render_template('menu_edit.html', self._conf, menu=menu_entries_for_event(self._conf))


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
