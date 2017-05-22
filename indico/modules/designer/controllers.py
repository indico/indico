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

import shutil
from io import BytesIO

from flask import flash, jsonify, request, session
from PIL import Image
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.legacy.webinterface.rh.base import RHModificationBaseProtected, check_event_locked
from indico.modules.categories.controllers.management import RHManageCategoryBase
from indico.modules.designer import DEFAULT_CONFIG
from indico.modules.designer.forms import AddTemplateForm
from indico.modules.designer.models.images import DesignerImageFile
from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.designer.util import get_inherited_templates, get_placeholder_options
from indico.modules.designer.views import WPCategoryManagementDesigner, WPEventManagementDesigner
from indico.modules.events import Event
from indico.modules.events.management.controllers import RHManageEventBase
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_data, jsonify_form


TEMPLATE_DATA_JSON_SCHEMA = {
    'type': 'object',
    'properties': {
        'width': {'type': 'integer', 'minimum': 0},
        'height': {'type': 'integer', 'minimum': 0},
        'background_position': {'type': 'string'},
        'items': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'text': {'type': 'string'},
                    'x': {'type': 'number', 'minimum': 0},
                    'y': {'type': 'number', 'minimum': 0},
                    'width': {'type': 'integer', 'minimum': 0},
                    'color': {'type': 'string'},
                    'font_family': {'type': 'string'},
                    'font_size': {'type': 'string'},
                    'text_align': {'type': 'string'},
                    'bold': {'type': 'boolean'},
                    'italic': {'type': 'boolean'}
                }
            },
            'required': ['id', 'text', 'x', 'y', 'width', 'color', 'font_family', 'font_size', 'text_align',
                         'bold', 'italic']
        },
    },
    'required': ['width', 'height', 'background_position', 'items']
}


def _render_template_list(target, event):
    tpl = get_template_module('designer/_list.html')
    return tpl.render_template_list(target.designer_templates, target, event=event,
                                    inherited_templates=get_inherited_templates(target))


class TemplateDesignerMixin:
    """
    Basic class for all template designer mixins.

    It resolves the target object type from the blueprint URL.
    """
    @property
    def object_type(self):
        """Figure out whether we're targetting an event or category, based on URL info."""
        return request.view_args['object_type']

    @property
    def event_or_none(self):
        return self.target if self.object_type == 'event' else None

    def _render_template(self, tpl_name, **kwargs):
        view_class = WPEventManagementDesigner if self.object_type == 'event' else WPCategoryManagementDesigner
        return view_class.render_template(tpl_name, self.target, 'designer', target=self.target, **kwargs)


class SpecificTemplateMixin(TemplateDesignerMixin):
    """
    Mixin that accepts a target template passed in the URL.

    The target category/event will be the owner of that template.
    """
    normalize_url_spec = {
        'locators': {
            lambda self: self.template
        }
    }

    @property
    def target(self):
        return self.template.owner

    def _checkProtection(self):
        if not self.target.can_manage(session.user):
            raise Forbidden
        elif isinstance(self.target, Event):
            check_event_locked(self, self.target)

    def _checkParams(self):
        self.template = DesignerTemplate.get_one(request.view_args['template_id'])


class TargetFromURLMixin(TemplateDesignerMixin):
    """
    Mixin that takes the target event/category from the URL that is passed.
    """

    @property
    def target_dict(self):
        return {'event_new': self.event_new} if self.object_type == 'event' else {'category': self.category}

    @property
    def target(self):
        return self.event_new if self.object_type == 'event' else self.category


class TemplateListMixin(TargetFromURLMixin):
    def _process(self):
        return self._render_template('list.html', inherited_templates=get_inherited_templates(self.target))


class CloneTemplateMixin(TargetFromURLMixin):
    def _checkProtection(self):
        if not self.target.can_manage(session.user):
            raise Forbidden

    def _checkParams(self):
        self.template = DesignerTemplate.get_one(request.view_args['template_id'])

    def _process(self):
        title = "{} (copy)".format(self.template.title)
        new_template = DesignerTemplate(title=title, type=self.template.type, data=self.template.data,
                                        **self.target_dict)

        if self.template.background_image:
            background = self.template.background_image
            new_background = DesignerImageFile(filename=background.filename, content_type=background.content_type,
                                               template=new_template)
            with background.open() as f:
                new_background.save(f)
        else:
            new_background = None

        new_template.background_image = new_background

        flash(_("Created copy of template '{}'").format(self.template.title), 'success')
        return jsonify_data(html=_render_template_list(self.target, event=self.event_or_none))


class AddTemplateMixin(TargetFromURLMixin):
    def _checkProtection(self):
        if not self.target.can_manage(session.user):
            raise Forbidden

    def _process(self):
        form = AddTemplateForm()
        if form.validate_on_submit():
            new_template = DesignerTemplate(title=form.title.data, type=form.type.data, **self.target_dict)
            flash(_("Added new template '{}'").format(new_template.title), 'success')
            return jsonify_data(html=_render_template_list(self.target, event=self.event_or_none))
        return jsonify_form(form, disabled_until_change=False)


class RHListEventTemplates(TemplateListMixin, RHManageEventBase):
    pass


class RHListCategoryTemplates(TemplateListMixin, RHManageCategoryBase):
    pass


class RHAddEventTemplate(AddTemplateMixin, RHManageEventBase):
    pass


class RHAddCategoryTemplate(AddTemplateMixin, RHManageCategoryBase):
    pass


class RHCloneEventTemplate(CloneTemplateMixin, RHManageEventBase):
    def _checkParams(self, params):
        RHManageEventBase._checkParams(self, params)
        CloneTemplateMixin._checkParams(self)


class RHCloneCategoryTemplate(CloneTemplateMixin, RHManageCategoryBase):
    def _checkParams(self, params):
        RHManageCategoryBase._checkParams(self)
        CloneTemplateMixin._checkParams(self)


class RHModifyDesignerTemplateBase(SpecificTemplateMixin, RHModificationBaseProtected):
    def _checkParams(self, params):
        RHModificationBaseProtected._checkParams(self, params)
        SpecificTemplateMixin._checkParams(self)


class RHEditDesignerTemplate(RHModifyDesignerTemplateBase):
    def _process_GET(self):
        return self._render_template('template.html', template=self.template, placeholders=get_placeholder_options(),
                                     config=DEFAULT_CONFIG[self.template.type], owner=self.target)

    def _process_POST(self):
        self.template.data = dict({'background_position': 'stretch', 'items': []}, **request.json['template'])
        self.template.title = request.json['title']
        self.validate_json(TEMPLATE_DATA_JSON_SCHEMA, self.template.data)

        if request.json.pop('clear_background'):
            self.template.background_image = None

        flash(_("Template successfully saved."), 'success')
        return jsonify_data()


class RHDownloadTemplateImage(RHModifyDesignerTemplateBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.image
        }
    }

    def _checkParams(self, params):
        RHModifyDesignerTemplateBase._checkParams(self, params)
        self.image = DesignerImageFile.find_one(id=request.view_args['image_id'], template=self.template)

    def _process(self):
        return self.image.send()


class RHUploadBackgroundImage(RHModifyDesignerTemplateBase):
    def _process(self):
        f = request.files['file']
        filename = secure_filename(f.filename, 'image')
        data = BytesIO()
        shutil.copyfileobj(f, data)
        data.seek(0)
        try:
            image_type = Image.open(data).format.lower()
        except IOError:
            # Invalid image data
            return jsonify(error="Invalid image data!")
        data.seek(0)
        if image_type not in {'jpeg', 'gif', 'png'}:
            return jsonify(error="File format not accepted!")
        content_type = 'image/' + image_type
        image = DesignerImageFile(template=self.template, filename=filename, content_type=content_type)
        self.template.background_image = image
        image.save(data)
        flash(_("The image has been uploaded"), 'success')
        return jsonify_data(image_url=image.download_url)


class RHDeleteDesignerTemplate(RHModifyDesignerTemplateBase):
    def _process(self):
        db.session.delete(self.template)
        flash(_('The template has been removed'), 'success')
        return jsonify_data(html=_render_template_list(self.target, event=self.event_or_none))
