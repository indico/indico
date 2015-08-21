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

import mimetypes
from io import BytesIO
from itertools import count

from flask import flash, redirect, request, session, jsonify, render_template
from werkzeug.exceptions import BadRequest, NotFound, Forbidden

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_default_values
from indico.modules.events.layout import layout_settings, logger
from indico.modules.events.layout.forms import (LayoutForm, MenuEntryForm, MenuLinkForm, MenuPageForm, AddImagesForm,
                                                CSSSelectionForm)
from indico.modules.events.layout.models.menu import MenuEntry, MenuEntryType, MenuPage
from indico.modules.events.layout.models.images import ImageFile
from indico.modules.events.layout.models.legacy_mapping import LegacyImageMapping
from indico.modules.events.layout.models.stylesheets import StylesheetFile
from indico.modules.events.layout.util import (get_event_logo, get_images_for_event, insert_entry,
                                               menu_entries_for_event, move_entry)
from indico.modules.events.layout.views import WPImages, WPLayoutEdit, WPMenuEdit, WPPage
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import redirect_or_jsonify, url_for, send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_template
from MaKaC.webinterface.pages.conferences import WPConfModifPreviewCSS
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


def _render_menu_entry(entry):
    tpl = get_template_module('events/layout/_menu.html')
    return tpl.menu_entry(entry=entry)


def _render_menu_entries(event, show_hidden=False, connect_menu=False):
    tpl = get_template_module('events/layout/_menu.html')
    return tpl.menu_entries(menu_entries_for_event(event, show_hidden=show_hidden), connect_menu=connect_menu)


class RHLayoutLogoUpload(RHConferenceModifBase):
    CSRF_ENABLED = True

    def _process(self):
        event = self._conf.as_event
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


class RHLayoutCSSUpload(RHConferenceModifBase):
    CSRF_ENABLED = True

    def _process(self):
        f = request.files['file']
        filename = secure_filename(f.filename, 'stylesheet.css')
        css_file = StylesheetFile(event_id=self._conf.id, filename=filename, content_type='text/css')
        css_file.save(f.file)
        db.session.add(css_file)
        db.session.flush()
        logger.info('CSS file {} uploaded by {}'.format(css_file, session.user))
        return jsonify({'success': True})


class RHLayoutCSSPreview(RHConferenceModifBase):
    def _process(self):
        theme = request.args.get('theme', '')
        return WPConfModifPreviewCSS(self, self._conf, theme).display()


class RHLayoutCSSSaveTheme(RHConferenceModifBase):
    CSRF_ENABLED = True

    def _process(self):
        form = CSSSelectionForm(event=self._conf)
        if form.validate_on_submit():
            layout_settings.set(self._conf, 'use_custom_css', form.theme.data == '_custom')
            if form.theme.data != '_custom':
                layout_settings.set(self._conf, 'theme', form.theme.data)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('event_layout.index', self._conf))


class RHLogoDisplay(RHConferenceBaseDisplay):
    def _process(self):
        logo_data = get_event_logo(self._conf)
        logo_content = BytesIO(logo_data['content'])
        metadata = logo_data['metadata']
        return send_file(metadata['file_name'], logo_content, mimetype=metadata['content_type'], no_cache=True,
                         conditional=True)


class RHLayoutCSSDisplay(RHConferenceBaseDisplay):
    normalize_url_spec = {
        'locators': {
            lambda self: self.css
        }
    }

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        css_id = request.view_args['css_id']
        self.css = StylesheetFile.get_one(css_id)

    def _process(self):
        return self.css.send()


class RHLayoutEdit(RHConferenceModifBase):
    def _checkProtection(self):
        RHConferenceModifBase._checkProtection(self)
        if self._conf.getType() != 'conference':
            raise NotFound('Only conferences have layout settings')

    def _process(self):
        defaults = FormDefaults(**layout_settings.get_all(self._conf))
        event = self._conf.as_event
        form = LayoutForm(event=event, obj=defaults)
        if form.validate_on_submit():
            data = {unicode(key): value for key, value in form.data.iteritems() if key in layout_settings.defaults}
            layout_settings.set_multi(self._conf, data)
            if form.theme.data == '_custom':
                layout_settings.set(self._conf, 'use_custom_css', True)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('event_layout.index', self._conf))
        else:
            if event.logo:
                form.logo.data = {
                    'url': url_for('event_images.logo_display', self._conf),
                    'file_name': event.logo_metadata['file_name'],
                    'size': event.logo_metadata['size'],
                    'content_type': event.logo_metadata['content_type']
                }
            css_file = StylesheetFile.find(StylesheetFile.event_id == self._conf.id).first()
            if css_file:
                form.css_file.data = {
                    'file_name': css_file.filename,
                    'size': css_file.size,
                    'content_type': css_file.content_type
                }
        return WPLayoutEdit.render_template('layout.html', self._conf, form=form, event=self._conf)


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
        menu = menu_entries_for_event(self._conf, show_hidden=True) if custom_menu_enabled else None
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
            if self.entry.type not in (MenuEntryType.user_link, MenuEntryType.page):
                raise BadRequest('Menu entry {0.title} cannot be moved to another menu: Invalid type {0.type.name}.'
                                 .format(self.entry))
            if self.entry.is_root and self.entry.children:
                raise BadRequest('Menu entry {entry.title} cannot be moved to another menu: Entry has nested entries.'
                                 .format(self.entry))

            if parent_id is not None:
                parent_entry = MenuEntry.find_first(MenuEntry.type.in_({MenuEntryType.user_link, MenuEntryType.page}),
                                                    id=parent_id, parent_id=None)
                if not parent_entry:
                    raise NotFound('New parent entry not found for Menu entry {entry.title}.'.format(entry=self.entry))

            insert_entry(self.entry, parent_id, position)

        else:
            move_entry(self.entry, position)

        return jsonify_data()


class RHMenuEnableEntry(RHMenuEntryEditBase):
    def _process(self):
        self.entry.is_enabled = not self.entry.is_enabled
        return redirect_or_jsonify(url_for('.menu', self._conf), is_enabled=self.entry.is_enabled)


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
            return jsonify_data(entry=_render_menu_entry(entry))

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
                entry.page = MenuPage(html=form.html.data)

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

        return jsonify_data(menu=_render_menu_entries(self._conf, show_hidden=True, connect_menu=True))


class RHPageDisplay(RHConferenceBaseDisplay):
    normalize_url_spec = {
        'locators': {
            lambda self: self.page
        }
    }

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.page = MenuPage.get_one(request.view_args['page_id'])

    def _process(self):
        return WPPage.render_template('events/layout/page.html', self._conf, page=self.page)


def _render_image_list(event):
    return render_template('events/layout/image_list.html', images=get_images_for_event(event))


class RHManageImagesBase(RHConferenceModifBase):
    EVENT_FEATURE = 'images'


class RHImages(RHManageImagesBase):
    def _process(self):
        form = AddImagesForm()
        return WPImages.render_template('images.html', self._conf, images=get_images_for_event(self._conf),
                                        event=self._conf, form=form)


class RHImageUpload(RHManageImagesBase):
    CSRF_ENABLED = True

    def _process(self):
        files = request.files.getlist('file')

        for f in files:
            filename = secure_filename(f.filename, 'image')
            content_type = mimetypes.guess_type(f.filename)[0] or f.mimetype or 'application/octet-stream'
            image = ImageFile(event_id=self._conf.id, filename=filename, content_type=content_type)
            image.save(f.file)
            db.session.add(image)
            db.session.flush()
            logger.info('Image {} uploaded by {}'.format(image, session.user))
            signals.event_management.image_created.send(image, user=session.user)
        flash(ngettext("The image has been uploaded", "{count} images have been uploaded", len(files))
              .format(count=len(files)), 'success')
        return jsonify_data(image_list=_render_image_list(self._conf))


class RHImageDelete(RHManageImagesBase):
    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHManageImagesBase._checkParams(self, params)
        self.image = ImageFile.find_first(id=request.view_args['image_id'], event_id=self._conf.getId())
        if not self.image:
            raise NotFound

    def _process(self):
        signals.event_management.image_deleted.send(self.image, user=session.user)
        db.session.delete(self.image)
        flash(_("The image '{}' has been deleted").format(self.image.filename), 'success')
        return jsonify_data(image_list=_render_image_list(self._conf))


class RHImageDisplay(RHConferenceBaseDisplay):
    EVENT_FEATURE = 'images'
    normalize_url_spec = {
        'locators': {
            lambda self: self.image
        }
    }

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        image_id = request.view_args['image_id']
        self.image = ImageFile.get_one(image_id)

    def _process(self):
        return self.image.send()


class RHImageLegacyDisplay(RHConferenceBaseDisplay):
    EVENT_FEATURE = 'images'

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.pic_id = request.view_args['pic_id']

    def _process(self):
        legacy_image = LegacyImageMapping.find_first(event_id=self._conf.id, legacy_image_id=self.pic_id)
        if legacy_image:
            return redirect(url_for('event_images.image_display', legacy_image.image), 301)
        else:
            raise NotFound
