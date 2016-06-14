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
from operator import attrgetter

from flask import flash, redirect, request, session
from PIL import Image
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import BadRequest

from indico.modules.categories import logger
from indico.modules.categories.controllers.base import RHManageCategoryBase
from indico.modules.categories.forms import (CategoryIconForm, CategoryLogoForm, CategoryProtectionForm,
                                             CategorySettingsForm, CreateCategoryForm)
from indico.modules.categories.models.categories import Category
from indico.modules.categories.operations import create_category, delete_category, update_category
from indico.modules.categories.views import WPCategoryManagement
from indico.modules.events.util import update_object_principals
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.util.string import crc32
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


CATEGORY_ICON_DIMENSIONS = (16, 16)


def _get_image_data(category, image_type):
    url = getattr(category, image_type + '_url')
    metadata = getattr(category, image_type + '_metadata')
    return {
        'url': url,
        'filename': metadata['filename'],
        'size': metadata['size'],
        'content_type': metadata['content_type']
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
                                                    subcategories=self.category.children,
                                                    events=self.category.events)


class RHManageCategorySettings(RHManageCategoryBase):
    def _process(self):
        defaults = FormDefaults(self.category,
                                meeting_theme=self.category.default_event_themes['meeting'],
                                lecture_theme=self.category.default_event_themes['lecture'])
        form = CategorySettingsForm(obj=defaults, category=self.category)
        icon_form = CategoryIconForm(obj=self.category)
        logo_form = CategoryLogoForm(obj=self.category)

        if form.validate_on_submit():
            update_category(self.category, form.data, skip={'meeting_theme', 'lecture_theme'})
            self.category.default_event_themes = {
                'meeting': form.meeting_theme.data,
                'lecture': form.lecture_theme.data
            }
            flash(_("Category settings saved!"), 'success')
            return redirect(url_for('.manage_settings', self.category))
        else:
            if self.category.icon_metadata:
                icon_form.icon.data = _get_image_data(self.category, 'icon')
            if self.category.logo_metadata:
                logo_form.logo.data = _get_image_data(self.category, 'logo')
        return WPCategoryManagement.render_template('management/settings.html', self.category, 'settings', form=form,
                                                    icon_form=icon_form, logo_form=logo_form)


class RHCategoryImageUploadBase(RHManageCategoryBase):
    IMAGE_TYPE = None
    SAVED_FLASH_MSG = None
    DELETED_FLASH_MSG = None

    def _resize(self, img):
        return img

    def _set_image(self, data, metadata):
        raise NotImplementedError

    def _process_POST(self):
        f = request.files['file']
        try:
            img = Image.open(f)
        except IOError:
            flash(_('You cannot upload this file as an icon/logo.'), 'error')
            return jsonify_data(content=None)
        if img.format.lower() not in {'jpeg', 'png', 'gif'}:
            flash(_('The file has an invalid format ({format})').format(format=img.format), 'error')
            return jsonify_data(content=None)
        if img.mode == 'CMYK':
            flash(_('The image you uploaded is using the CMYK colorspace and has been converted to RGB.  '
                    'Please check if the colors are correct and convert it manually if necessary.'), 'warning')
            img = img.convert('RGB')
        img = self._resize(img)
        image_bytes = BytesIO()
        img.save(image_bytes, 'PNG')
        image_bytes.seek(0)
        content = image_bytes.read()
        metadata = {
            'hash': crc32(content),
            'size': len(content),
            'filename': os.path.splitext(secure_filename(f.filename, self.IMAGE_TYPE))[0] + '.png',
            'content_type': 'image/png'
        }
        self._set_image(content, metadata)
        flash(self.SAVED_FLASH_MSG, 'success')
        logger.info("New {} '%s' uploaded by %s (%s)".format(self.IMAGE_TYPE), f.filename, session.user, self.category)
        return jsonify_data(content=_get_image_data(self.category, self.IMAGE_TYPE))

    def _process_DELETE(self):
        self._set_image(None, None)
        flash(self.DELETED_FLASH_MSG, 'success')
        logger.info("{} of %s deleted by %s".format(self.IMAGE_TYPE.title()), self.category, session.user)
        return jsonify_data(content=None)


class RHManageCategoryIcon(RHCategoryImageUploadBase):
    IMAGE_TYPE = 'icon'
    SAVED_FLASH_MSG = _('New icon saved')
    DELETED_FLASH_MSG = _('Icon deleted')

    def _resize(self, img):
        if img.size != CATEGORY_ICON_DIMENSIONS:
            img = img.resize(CATEGORY_ICON_DIMENSIONS, Image.ANTIALIAS)
        return img

    def _set_image(self, data, metadata):
        self.category.icon = data
        self.category.icon_metadata = metadata


class RHManageCategoryLogo(RHCategoryImageUploadBase):
    IMAGE_TYPE = 'logo'
    SAVED_FLASH_MSG = _('New logo saved')
    DELETED_FLASH_MSG = _('Logo deleted')

    def _set_image(self, data, metadata):
        self.category.logo = data
        self.category.logo_metadata = metadata


class RHManageCategoryProtection(RHManageCategoryBase):
    def _process(self):
        form = CategoryProtectionForm(obj=self._get_defaults(), category=self.category)
        if form.validate_on_submit():
            update_category(self.category,
                            {'protection_mode': form.protection_mode.data,
                             'own_no_access_contact': form.own_no_access_contact.data,
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


class RHCreateCategory(RHManageCategoryBase):
    def _process(self):
        form = CreateCategoryForm()
        if form.validate_on_submit():
            new_category = create_category(self.category, form.data)
            flash(_('Category "{}" has been created.').format(new_category.title), 'success')
            return jsonify_data(flash=False, redirect=url_for('.manage_settings', new_category))
        return jsonify_form(form)


class RHDeleteCategory(RHManageCategoryBase):
    def _process(self):
        if self.category.is_root:
            raise BadRequest('The root category cannot be deleted')
        if not self.category.is_empty:
            raise BadRequest('Cannot delete a non-empty category')
        delete_category(self.category)
        url = url_for('.manage_content', self.category.parent)
        if request.is_xhr:
            return jsonify_data(flash=False, redirect=url, is_parent_empty=self.category.parent.is_empty)
        else:
            flash(_('Category "{}" has been deleted.').format(self.category.title), 'success')
            return redirect(url)


class RHCategoryMoveContents(RHManageCategoryBase):
    def _process(self):
        return jsonify_template('categories/management/move_category_contents.html', category=self.category)


class RHDeleteSubcategories(RHManageCategoryBase):
    """Bulk-delete subcategories"""

    def _checkParams(self):
        RHManageCategoryBase._checkParams(self)
        self.subcategories = (Category.query
                              .with_parent(self.category)
                              .filter(Category.id.in_(map(int, request.form.getlist('category_id'))))
                              .all())

    def _process(self):
        if 'confirmed' in request.form:
            for subcategory in self.subcategories:
                if not subcategory.is_empty:
                    raise BadRequest('Category "{}" is not empty'.format(subcategory.title))
                delete_category(subcategory)
            return jsonify_data(flash=False, is_empty=self.category.is_empty)
        return jsonify_template('categories/management/delete_categories.html', categories=self.subcategories,
                                category_ids=[x.id for x in self.subcategories])


class RHSortSubcategories(RHManageCategoryBase):
    def _process(self):
        subcategories = {category.id: category for category in self.category.children}
        for position, id_ in enumerate(request.json['categories'], 1):
            subcategories[id_].position = position
