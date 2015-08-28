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

from itertools import count

from flask import flash, request, session, jsonify
from werkzeug.exceptions import BadRequest, NotFound, Forbidden

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_default_values
from indico.modules.events.layout import layout_settings, logger
from indico.modules.events.layout.forms import (MenuEntryForm, MenuLinkForm, MenuPageForm)
from indico.modules.events.layout.models.menu import MenuEntry, MenuEntryType, EventPage
from indico.modules.events.layout.util import menu_entries_for_event
from indico.modules.events.layout.views import WPMenuEdit, WPPage
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_template
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


def _render_menu_entry(entry):
    tpl = get_template_module('events/layout/_menu.html')
    return tpl.menu_entry(entry=entry)


def _render_menu_entries(event, connect_menu=False):
    tpl = get_template_module('events/layout/_menu.html')
    return tpl.menu_entries(menu_entries_for_event(event), connect_menu=connect_menu)


class RHMenuBase(RHConferenceModifBase):
    CSRF_ENABLED = True

    def _checkProtection(self):
        RHConferenceModifBase._checkProtection(self)
        if self._conf.getType() != 'conference':
            raise NotFound('Only conferences have a menu')

    def _require_custom_menu(self):
        if not layout_settings.get(self._conf, 'use_custom_menu'):
            raise Forbidden('The menu cannot be changed unless menu customization is enabled')


class RHMenuEdit(RHMenuBase):
    def _process(self):
        custom_menu_enabled = layout_settings.get(self._conf, 'use_custom_menu')
        menu = menu_entries_for_event(self._conf) if custom_menu_enabled else None
        return WPMenuEdit.render_template('menu_edit.html', self._conf, event=self._conf, MenuEntryType=MenuEntryType,
                                          menu=menu, custom_menu_enabled=custom_menu_enabled)


class RHMenuToggleCustom(RHMenuBase):
    def _process(self):
        enabled = request.form['enabled'] == '1'
        if enabled:
            # nothing else to do here. menu items are added to the DB when retrieving the menu
            flash(_('Menu customization has been enabled.'), 'success')
        else:
            for entry in MenuEntry.find(event_id=int(self._conf.id)):
                db.session.delete(entry)
            flash(_('Menu customization has been disabled.'), 'success')
        layout_settings.set(self._conf, 'use_custom_menu', enabled)
        logger.info('Menu customization for {} {} by {}'.format(self._conf, 'enabled' if enabled else 'disabled',
                                                                session.user))
        return jsonify(enabled=enabled)


class RHMenuEntryEditBase(RHMenuBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.entry
        }
    }

    def _checkProtection(self):
        RHMenuBase._checkProtection(self)
        self._require_custom_menu()

    def _checkParams(self, params):
        RHMenuBase._checkParams(self, params)
        self.entry = MenuEntry.get_one(request.view_args['menu_entry_id'])


class RHMenuEntryEdit(RHMenuEntryEditBase):
    def _process(self):
        defaults = FormDefaults(self.entry)
        form_cls = MenuEntryForm
        if self.entry.is_user_link:
            form_cls = MenuLinkForm
        elif self.entry.is_page:
            form_cls = MenuPageForm
            defaults['html'] = self.entry.page.html
        form = form_cls(linked_object=self.entry, obj=defaults)
        if form.validate_on_submit():
            form.populate_obj(self.entry, skip={'html'})
            if self.entry.is_page:
                self.entry.page.html = form.html.data
            return jsonify_data(entry=_render_menu_entry(self.entry))
        return jsonify_template('events/layout/menu_entry_form.html', form=form)


class RHMenuEntryPosition(RHMenuEntryEditBase):
    def _process(self):
        position = request.form.get('position')
        try:
            position = int(position)
        except (TypeError, ValueError):
            position = None

        parent_id = request.form.get('parent_id')
        try:
            parent_id = int(parent_id)
        except (TypeError, ValueError):
            parent_id = None

        if parent_id != self.entry.parent_id:
            if self.entry.type not in {MenuEntryType.user_link, MenuEntryType.page}:
                raise BadRequest('Menu entry "{0.title}" cannot be moved to another menu: Invalid type "{0.type.name}".'
                                 .format(self.entry))
            if self.entry.is_root and self.entry.children:
                raise BadRequest('Menu entry "{0.title}" cannot be moved to another menu: Entry has nested entries.'
                                 .format(self.entry))

            if parent_id is not None:
                parent_entry = MenuEntry.find_first(MenuEntry.type.in_({MenuEntryType.user_link, MenuEntryType.page}),
                                                    id=parent_id, parent_id=None, event_id=self.entry.event_id)
                if not parent_entry:
                    raise BadRequest('New parent entry not found for Menu entry "{0.title}".'.format(self.entry))

            self.entry.insert(parent_id, position)

        else:
            self.entry.move(position)

        return jsonify_data(flash=False)


class RHMenuEntryToggleEnabled(RHMenuEntryEditBase):
    def _process(self):
        self.entry.is_enabled = not self.entry.is_enabled
        return jsonify(is_enabled=self.entry.is_enabled)


class RHMenuEntryToggleDefault(RHMenuEntryEditBase):
    def _process(self):
        if self.entry.type != MenuEntryType.page:
            raise BadRequest
        event = self._conf.as_event
        if event.default_page_id == self.entry.page_id:
            is_default = False
            event.default_page_id = None
        else:
            is_default = True
            event.default_page_id = self.entry.page_id
        return jsonify(is_default=is_default)


class RHMenuAddEntry(RHMenuBase):
    def _checkProtection(self):
        RHMenuBase._checkProtection(self)
        self._require_custom_menu()

    def _process(self):
        defaults = FormDefaults(get_default_values(MenuEntry))
        entry_type = request.args['type']

        if entry_type == MenuEntryType.separator.name:
            entry = MenuEntry(event_id=self._conf.id, type=MenuEntryType.separator)
            db.session.add(entry)
            db.session.flush()
            return jsonify_data(flash=False, entry=_render_menu_entry(entry))

        elif entry_type == MenuEntryType.user_link.name:
            form_cls = MenuLinkForm
        elif entry_type == MenuEntryType.page.name:
            form_cls = MenuPageForm
        else:
            raise BadRequest

        form = form_cls(obj=defaults)
        if form.validate_on_submit():
            entry = MenuEntry(
                event_id=self._conf.id,
                type=MenuEntryType[entry_type]
            )
            form.populate_obj(entry, skip={'html'})

            if entry.is_page:
                page = EventPage(html=form.html.data)
                self._conf.as_event.custom_pages.append(page)
                entry.page = page

            db.session.add(entry)
            db.session.flush()
            return jsonify_data(entry=_render_menu_entry(entry))
        return jsonify_template('events/layout/menu_entry_form.html', form=form)


class RHMenuDeleteEntry(RHMenuEntryEditBase):
    def _process(self):
        if self.entry.type not in (MenuEntryType.user_link, MenuEntryType.page, MenuEntryType.separator):
            raise BadRequest('Menu entry of type {} cannot be deleted'.format(self.entry.type.name))

        position_gen = count(self.entry.position)
        if self.entry.children:
            for child in self.entry.children:
                child.parent_id = self.entry.parent_id
                child.position = next(position_gen)

        with db.session.no_autoflush:
            entries = MenuEntry.find_all(MenuEntry.event_id == self.entry.event_id,
                                         MenuEntry.parent_id == self.entry.parent_id,
                                         MenuEntry.position >= self.entry.position,
                                         MenuEntry.id != self.entry.id)
        for entry in entries:
            entry.position = next(position_gen)

        db.session.delete(self.entry)
        db.session.flush()

        return jsonify_data(flash=False, menu=_render_menu_entries(self._conf, connect_menu=True))


class RHPageDisplay(RHConferenceBaseDisplay):
    normalize_url_spec = {
        'locators': {
            lambda self: self.page
        }
    }

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.page = EventPage.get_one(request.view_args['page_id'])

    def _process(self):
        return WPPage.render_template('page.html', self._conf, page=self.page)
