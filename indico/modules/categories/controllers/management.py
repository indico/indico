# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
from sqlalchemy.orm import joinedload

from indico.modules.events.util import update_object_principals
from indico.modules.categories import logger
from indico.modules.categories.controllers.base import RHManageCategoryBase
from indico.modules.categories.forms import CategoryIconForm, CategoryProtectionForm, CategorySettingsForm
from indico.modules.categories.operations import update_category
from indico.modules.categories.views import WPCategoryManagement
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.util.string import crc32
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data


CATEGORY_ICON_DIMENSIONS = (16, 16)


def _icon_data(category):
    return {
        'url': category.icon_url,
        'filename': category.icon_metadata['filename'],
        'size': category.icon_metadata['size'],
        'content_type': category.icon_metadata['content_type']
    }


class RHManageCategoryContent(RHManageCategoryBase):
    @property
    def _category_query_options(self):
        children_strategy = joinedload('children')
        children_strategy.undefer('deep_children_count')
        children_strategy.undefer('deep_events_count')
        return children_strategy,

    def _process(self):
        return WPCategoryManagement.render_template('management/content.html', self.category, 'content',
                                                    categories=self.category.children)


class RHManageCategorySettings(RHManageCategoryBase):
    def _process(self):
        defaults = FormDefaults(self.category,
                                meeting_theme=self.category.default_event_themes['meeting'],
                                lecture_theme=self.category.default_event_themes['lecture'])
        form = CategorySettingsForm(obj=defaults, category=self.category)
        icon_form = CategoryIconForm(obj=self.category)

        if form.validate_on_submit():
            update_category(self.category, form.data, skip={'meeting_theme', 'lecture_theme'})
            self.category.default_event_themes = {
                'meeting': form.meeting_theme.data,
                'lecture': form.meeting_theme.data
            }
            flash(_("Category settings saved!"), 'success')
            return redirect(url_for('.manage_settings', self.category))
        else:
            if self.category.icon_metadata:
                icon_form.icon.data = _icon_data(self.category)
        return WPCategoryManagement.render_template('management/settings.html', self.category, 'settings', form=form,
                                                    icon_form=icon_form)


class RHSettingsIconUpload(RHManageCategoryBase):
    def _process_POST(self):
        f = request.files['file']
        try:
            img = Image.open(f)
        except IOError:
            flash(_('You cannot upload this file as an icon.'), 'error')
            return jsonify_data(content=None)
        if img.format.lower() not in {'jpeg', 'png', 'gif'}:
            flash(_('The file has an invalid format ({format})').format(format=img.format), 'error')
            return jsonify_data(content=None)
        if img.mode == 'CMYK':
            flash(_('The icon you uploaded is using the CMYK colorspace and has been converted to RGB. Please check if '
                    'the colors are correct and convert it manually if necessary.'), 'warning')
            img = img.convert('RGB')
        if img.size != CATEGORY_ICON_DIMENSIONS:
            img = img.resize(CATEGORY_ICON_DIMENSIONS, Image.ANTIALIAS)
        image_bytes = BytesIO()
        img.save(image_bytes, 'PNG')
        image_bytes.seek(0)
        content = image_bytes.read()
        self.category.icon = content
        self.category.icon_metadata = {
            'hash': crc32(content),
            'size': len(content),
            'filename': os.path.splitext(secure_filename(f.filename, 'icon'))[0] + '.png',
            'content_type': 'image/png'
        }
        flash(_('New icon saved'), 'success')
        logger.info("New icon '%s' uploaded by %s (%s)", f.filename, session.user, self.category)
        return jsonify_data(content=_icon_data(self.category))

    def _process_DELETE(self):
        self.category.icon = None
        self.category.icon_metadata = None
        flash(_('Icon deleted'), 'success')
        logger.info("Icon of %s deleted by %s", self.category, session.user)
        return jsonify_data(content=None)


class RHManageCategoryProtection(RHManageCategoryBase):
    def _process(self):
        form = CategoryProtectionForm(obj=self._get_defaults(), category=self.category)
        if form.validate_on_submit():
            update_category(self.category,
                            {'protection_mode': form.protection_mode.data,
                             'no_access_contact': form.no_access_contact.data,
                             'event_creation_restricted': form.event_creation_restricted.data})
            update_object_principals(self.category, form.acl.data, read_access=True)
            update_object_principals(self.category, form.managers.data, full_access=True)
            update_object_principals(self.category, form.event_creators.data, role='create')
            flash(_('Protection settings of the category have been updated'), 'success')
            return redirect(url_for('.manage_protection', self.category))
        return WPCategoryManagement.render_template('management/category_protection.html', self.category, 'protection',
                                                    form=form)

    def _get_defaults(self):
        acl = {x.principal for x in self.category.acl_entries if x.read_access}
        managers = {x.principal for x in self.category.acl_entries if x.full_access}
        event_creators = {x.principal for x in self.category.acl_entries
                          if x.has_management_role('create', explicit=True)}
        return FormDefaults(self.category, acl=acl, managers=managers, event_creators=event_creators)
