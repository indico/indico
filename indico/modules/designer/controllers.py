# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
from collections import defaultdict
from io import BytesIO

from flask import flash, jsonify, request, session
from PIL import Image
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.core.errors import UserValueError
from indico.modules.categories import Category
from indico.modules.categories.controllers.management import RHManageCategoryBase
from indico.modules.designer import DEFAULT_CONFIG, TemplateType
from indico.modules.designer.forms import AddTemplateForm
from indico.modules.designer.models.images import DesignerImageFile
from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.designer.operations import update_template
from indico.modules.designer.util import (get_all_templates, get_default_template_on_category, get_inherited_templates,
                                          get_nested_placeholder_options, get_not_deletable_templates,
                                          get_placeholder_options)
from indico.modules.designer.views import WPCategoryManagementDesigner, WPEventManagementDesigner
from indico.modules.events import Event
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.util import check_event_locked
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.rh import RHProtected
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


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


def _render_template_list(target, event=None):
    tpl = get_template_module('designer/_list.html')
    default_template = get_default_template_on_category(target) if isinstance(target, Category) else None
    not_deletable = get_not_deletable_templates(target)
    return tpl.render_template_list(target.designer_templates, target, event=event, default_template=default_template,
                                    inherited_templates=get_inherited_templates(target),
                                    not_deletable_templates=not_deletable)


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

    def _check_access(self):
        self._require_user()
        if not self.target.can_manage(session.user):
            raise Forbidden
        elif isinstance(self.target, Event):
            check_event_locked(self, self.target)

    def _process_args(self):
        self.template = DesignerTemplate.get_one(request.view_args['template_id'])


class TargetFromURLMixin(TemplateDesignerMixin):
    """
    Mixin that takes the target event/category from the URL that is passed.
    """

    @property
    def target_dict(self):
        return {'event': self.event} if self.object_type == 'event' else {'category': self.category}

    @property
    def target(self):
        return self.event if self.object_type == 'event' else self.category


class TemplateListMixin(TargetFromURLMixin):
    def _process(self):
        templates = get_inherited_templates(self.target)
        not_deletable = get_not_deletable_templates(self.target)
        default_template = get_default_template_on_category(self.target) if isinstance(self.target, Category) else None
        return self._render_template('list.html', inherited_templates=templates, not_deletable_templates=not_deletable,
                                     default_template=default_template,)


class CloneTemplateMixin(TargetFromURLMixin):
    def _check_access(self):
        if not self.target.can_manage(session.user):
            raise Forbidden

    def _process_args(self):
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
    always_clonable = False

    def _check_access(self):
        if not self.target.can_manage(session.user):
            raise Forbidden

    def _process(self):
        form = AddTemplateForm()
        if self.always_clonable:
            del form.is_clonable
        if form.validate_on_submit():
            is_clonable = form.is_clonable.data if form.is_clonable else True
            new_template = DesignerTemplate(title=form.title.data, type=form.type.data, is_clonable=is_clonable,
                                            **self.target_dict)
            flash(_("Added new template '{}'").format(new_template.title), 'success')
            return jsonify_data(html=_render_template_list(self.target, event=self.event_or_none))
        return jsonify_form(form, disabled_until_change=False)


class RHListEventTemplates(TemplateListMixin, RHManageEventBase):
    pass


class RHListCategoryTemplates(TemplateListMixin, RHManageCategoryBase):
    pass


class RHAddEventTemplate(AddTemplateMixin, RHManageEventBase):
    always_clonable = True


class RHAddCategoryTemplate(AddTemplateMixin, RHManageCategoryBase):
    always_clonable = False


class RHCloneEventTemplate(CloneTemplateMixin, RHManageEventBase):
    def _process_args(self):
        RHManageEventBase._process_args(self)
        CloneTemplateMixin._process_args(self)


class RHCloneCategoryTemplate(CloneTemplateMixin, RHManageCategoryBase):
    def _process_args(self):
        RHManageCategoryBase._process_args(self)
        CloneTemplateMixin._process_args(self)


class RHModifyDesignerTemplateBase(SpecificTemplateMixin, RHProtected):
    def _check_access(self):
        RHProtected._check_access(self)
        SpecificTemplateMixin._check_access(self)


class RHEditDesignerTemplate(RHModifyDesignerTemplateBase):
    def _process_GET(self):
        bs_template = self.template.backside_template
        template_data = {
            'title': self.template.title,
            'data': self.template.data,
            'is_clonable': self.template.is_clonable,
            'background_url': self.template.background_image.download_url if self.template.background_image else None
        }
        backside_template_data = {
            'id': bs_template.id if bs_template else None,
            'title': bs_template.title if bs_template else None,
            'data': bs_template.data if bs_template else None,
            'background_url': (bs_template.background_image.download_url
                               if bs_template and bs_template.background_image else None)
        }
        backside_templates = (DesignerTemplate.query
                              .filter(DesignerTemplate.backside_template_id == self.template.id)
                              .all())
        related_tpls_per_owner = defaultdict(list)
        for bs_tpl in backside_templates:
            related_tpls_per_owner[bs_tpl.owner].append(bs_tpl)
        return self._render_template('template.html', template=self.template,
                                     placeholders=get_nested_placeholder_options(),
                                     config=DEFAULT_CONFIG[self.template.type], owner=self.target,
                                     template_data=template_data, backside_template_data=backside_template_data,
                                     related_tpls_per_owner=related_tpls_per_owner, tpls_count=len(backside_templates))

    def _process_POST(self):
        data = dict({'background_position': 'stretch', 'items': []}, **request.json['template'])
        self.validate_json(TEMPLATE_DATA_JSON_SCHEMA, data)
        invalid_placeholders = {x['type'] for x in data['items']} - set(get_placeholder_options()) - {'fixed'}
        if invalid_placeholders:
            raise UserValueError('Invalid item types: {}'.format(', '.join(invalid_placeholders)))
        update_template(self.template, title=request.json['title'], data=data,
                        backside_template_id=request.json['backside_template_id'],
                        is_clonable=request.json['is_clonable'],
                        clear_background=request.json['clear_background'])
        flash(_("Template successfully saved."), 'success')
        return jsonify_data()


class RHDownloadTemplateImage(RHModifyDesignerTemplateBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.image
        }
    }

    def _process_args(self):
        RHModifyDesignerTemplateBase._process_args(self)
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
        root = Category.get_root()
        if not root.default_ticket_template:
            # if we deleted the root category's default template, pick
            # a system template as the new default (this always exists)
            system_template = DesignerTemplate.find_first(DesignerTemplate.is_system_template,
                                                          DesignerTemplate.type == TemplateType.badge)
            root.default_ticket_template = system_template
        db.session.flush()
        flash(_('The template has been deleted'), 'success')
        return jsonify_data(html=_render_template_list(self.target, event=self.event_or_none))


class RHListBacksideTemplates(RHModifyDesignerTemplateBase, RHListEventTemplates):
    def _process(self):
        inherited_templates = [tpl for tpl in get_inherited_templates(self.target)
                               if not tpl.backside_template and tpl.type == TemplateType.badge]
        custom_templates = [tpl for tpl in self.target.designer_templates
                            if not tpl.backside_template and tpl != self.template and tpl.type == TemplateType.badge]
        return jsonify_template('designer/backside_list.html', target=self.target, custom_templates=custom_templates,
                                inherited_templates=inherited_templates, current_template=self.template,
                                width=int(request.args['width']), height=int(request.args['height']))


class RHGetTemplateData(RHModifyDesignerTemplateBase):
    def _process(self):
        template_data = {
            'title': self.template.title,
            'data': self.template.data,
            'background_url': self.template.background_image.download_url if self.template.background_image else None
        }
        return jsonify(template=template_data, backside_template_id=self.template.id)


class RHToggleTemplateDefaultOnCategory(RHManageCategoryBase):
    def _process(self):
        template = DesignerTemplate.get_one(request.view_args['template_id'])
        if template not in get_all_templates(self.category):
            raise Exception('Invalid template')
        if template == self.category.default_ticket_template:
            # already the default -> clear it
            self.category.default_ticket_template = None
        elif template == get_default_template_on_category(self.category, only_inherited=True):
            # already the inherited default -> clear it instead of setting it explicitly
            self.category.default_ticket_template = None
        else:
            self.category.default_ticket_template = template
        if self.category.is_root and not self.category.default_ticket_template:
            raise Exception('Cannot clear default ticket template on root category')
        return jsonify_data(html=_render_template_list(self.category))
