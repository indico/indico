# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import shutil
from collections import defaultdict
from copy import deepcopy
from io import BytesIO

from flask import flash, jsonify, request, session
from markupsafe import Markup
from PIL import Image
from reportlab.lib.colors import toColor
from webargs import fields
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from indico.core import signals
from indico.core.db import db
from indico.core.errors import UserValueError
from indico.modules.categories import Category
from indico.modules.categories.controllers.management import RHManageCategoryBase
from indico.modules.designer import DEFAULT_CONFIG, TemplateType
from indico.modules.designer.forms import AddTemplateForm, CloneTemplateForm
from indico.modules.designer.models.images import DesignerImageFile
from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.designer.operations import update_template
from indico.modules.designer.util import (can_link_to_regform, get_all_templates, get_default_badge_on_category,
                                          get_default_ticket_on_category, get_image_placeholder_types,
                                          get_inherited_templates, get_linkable_regforms,
                                          get_nested_placeholder_options, get_not_deletable_templates,
                                          get_placeholder_options)
from indico.modules.designer.views import WPCategoryManagementDesigner, WPEventManagementDesigner
from indico.modules.events import Event, EventLogRealm
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.util import check_event_locked
from indico.modules.logs import LogKind
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.util.marshmallow import ModelField
from indico.web.args import use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
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
                    'height': {
                        'anyOf': [
                            {'type': 'integer', 'minimum': 0},
                            {'type': 'null'},
                        ],
                    },
                    'width': {'type': 'integer', 'minimum': 0},
                    'color': {'type': 'string'},
                    'font_family': {'type': 'string'},
                    'font_size': {'type': 'string'},
                    'text_align': {'type': 'string'},
                    'bold': {'type': 'boolean'},
                    'italic': {'type': 'boolean'},
                    'preserve_aspect_ratio': {'type': 'boolean'}
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
    default_ticket = get_default_ticket_on_category(target) if isinstance(target, Category) else None
    default_badge = get_default_badge_on_category(target) if isinstance(target, Category) else None
    not_deletable = get_not_deletable_templates(target)
    linkable_forms = defaultdict(list)
    for template in target.designer_templates:
        linkable_forms[template] = get_linkable_regforms(template)

    return tpl.render_template_list(target.designer_templates, target, linkable_forms, event=event,
                                    default_ticket=default_ticket, default_badge=default_badge,
                                    inherited_templates=get_inherited_templates(target),
                                    not_deletable_templates=not_deletable)


class TemplateDesignerMixin:
    """Basic class for all template designer mixins.

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
    """Mixin that accepts a target template passed in the URL.

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
        self.template = DesignerTemplate.get_or_404(request.view_args['template_id'])
        if self.target.is_deleted:
            raise NotFound


class BacksideTemplateProtectionMixin:
    def _check_access(self):
        self._require_user()
        # Category templates can be used as backsides - we can't require management
        # or even read access to the category for this as someone may be managing an
        # event inside a category they can't access/manage.
        if isinstance(self.target, Event):
            SpecificTemplateMixin._check_access(self)


class TargetFromURLMixin(TemplateDesignerMixin):
    """Mixin that takes the target event/category from the URL that is passed."""

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
        default_ticket = get_default_ticket_on_category(self.target) if isinstance(self.target, Category) else None
        default_badge = get_default_badge_on_category(self.target) if isinstance(self.target, Category) else None
        signals.event.filter_selectable_badges.send(type(self), badge_templates=templates)
        signals.event.filter_selectable_badges.send(type(self), badge_templates=not_deletable)
        linkable_forms = defaultdict(list)
        for template in self.target.designer_templates:
            linkable_forms[template] = get_linkable_regforms(template)

        return self._render_template('list.html', inherited_templates=templates, not_deletable_templates=not_deletable,
                                     default_ticket=default_ticket, default_badge=default_badge,
                                     linkable_forms=linkable_forms)


class CloneTemplateMixin(TargetFromURLMixin):
    clonable_elsewhere = False

    def _check_access(self):
        if not self.target.can_manage(session.user):
            raise Forbidden

    def _process_args(self):
        self.template = DesignerTemplate.get_or_404(request.view_args['template_id'])

    def clone_template(self, target=None):
        title = f'{self.template.title} (copy)'
        target_dict = target or self.target_dict
        new_template = DesignerTemplate(title=title, type=self.template.type, **target_dict)

        data = deepcopy(self.template.data)
        image_items = [item for item in data['items'] if item['type'] == 'fixed_image']
        for image_item in image_items:
            old_image = DesignerImageFile.get(image_item['image_id'])
            new_image = DesignerImageFile(filename=old_image.filename, content_type=old_image.content_type,
                                          template=new_template)
            with old_image.open() as f:
                new_image.save(f)
            image_item['image_id'] = new_image.id
        new_template.data = data

        if self.template.registration_form:
            new_template.link_regform(self.template.registration_form)

        if self.template.background_image:
            background = self.template.background_image
            new_background = DesignerImageFile(filename=background.filename, content_type=background.content_type,
                                               template=new_template)
            with background.open() as f:
                new_background.save(f)
        else:
            new_background = None

        new_template.background_image = new_background

        message = _("Created copy of template '{}'").format(self.template.title)
        if target_dict != self.target_dict:
            message += Markup(' (<a href="{}">{}</a>)').format(url_for('designer.template_list',
                                                                       target_dict['category']),
                                                               _('Go to category'))
        flash(message, 'success')
        return jsonify_data(html=_render_template_list(self.target, event=self.event_or_none))

    def _process(self):
        if self.clonable_elsewhere:
            category = (self.target if isinstance(self.target, Category) and
                        self.target.can_manage(session.user) else None)
            form = CloneTemplateForm(category=category)
            if form.validate_on_submit():
                return self.clone_template(target=form.data)
            return jsonify_form(form, submit=_('Clone'), disabled_until_change=False)
        if request.method == 'POST':
            return self.clone_template()


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
    clonable_elsewhere = True

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
            'background_url': self.template.background_image.download_url if self.template.background_image else None,
            'images': {img.id: img.download_url for img in self.template.images} if self.template.images else None
        }
        backside_template_data = {
            'id': bs_template.id if bs_template else None,
            'title': bs_template.title if bs_template else None,
            'data': bs_template.data if bs_template else None,
            'background_url': (bs_template.background_image.download_url
                               if bs_template and bs_template.background_image else None),
            'images': ({img.id: img.download_url for img in bs_template.images}
                       if bs_template and bs_template.images else None)
        }
        backside_templates = (DesignerTemplate.query
                              .filter(DesignerTemplate.backside_template_id == self.template.id)
                              .all())
        related_tpls_per_owner = defaultdict(list)
        for bs_tpl in backside_templates:
            related_tpls_per_owner[bs_tpl.owner].append(bs_tpl)
        placeholders = get_nested_placeholder_options(regform=self.template.registration_form)
        return self._render_template('template.html', template=self.template,
                                     placeholders=placeholders,
                                     image_types=get_image_placeholder_types(self.template.registration_form),
                                     config=DEFAULT_CONFIG[self.template.type], owner=self.target,
                                     template_data=template_data, backside_template_data=backside_template_data,
                                     related_tpls_per_owner=related_tpls_per_owner, tpls_count=len(backside_templates))

    @use_kwargs({
        'backside': ModelField(DesignerTemplate, data_key='backside_template_id', load_default=None),
    })
    def _process_POST(self, backside):
        data = dict({'background_position': 'stretch', 'items': []}, **request.json['template'])
        self.validate_json(TEMPLATE_DATA_JSON_SCHEMA, data)
        if backside:
            self._validate_backside_template(backside)
        placeholders = get_placeholder_options(regform=self.template.registration_form)
        if invalid_placeholders := {x['type'] for x in data['items']} - set(placeholders):
            raise UserValueError('Invalid item types: {}'.format(', '.join(invalid_placeholders)))
        image_items = [item for item in data['items'] if item['type'] == 'fixed_image']
        template_images = {img.id for img in self.template.images}
        for image_item in image_items:
            if 'image_id' not in image_item:
                raise UserValueError(_('A Fixed Image element must contain an image'))
            if image_item['image_id'] not in template_images:
                raise UserValueError(_('The image file does not belong to this template'))
        for item in data['items']:
            if (color := item.get('color')) and not self._validate_color(color):
                item_name = placeholders[item['type']].description
                raise UserValueError(_('Invalid color in field "{}": {}').format(item_name, color))
            if (color := item.get('background_color')) and not self._validate_color(color):
                item_name = placeholders[item['type']].description
                raise UserValueError(_('Invalid background color in field "{}": {}').format(item_name, color))
        update_template(self.template, title=request.json['title'], data=data,
                        backside_template_id=request.json.get('backside_template_id'),
                        is_clonable=request.json['is_clonable'],
                        clear_background=request.json['clear_background'])
        flash(_('Template successfully saved.'), 'success')
        return jsonify_data()

    def _validate_color(self, color):
        try:
            toColor(color)
        except ValueError:
            return False
        return True

    def _validate_backside_template(self, backside_template):
        """Verify if the given template can be used as a backside for the current template.

        A template can be used as a backside if:
            - frontside != backside
            - backside does't already have its own backside
            - it has the same size as the frontside
            - the templates are linked to the same registration form or
              at least one template is not linked to any registration form
        """
        same_size = (
            self.template.data['width'] == backside_template.data['width'] and
            self.template.data['height'] == backside_template.data['height']
        )

        linked_to_same_regform = (
            not self.template.registration_form or
            not backside_template.registration_form or
            self.template.registration_form == backside_template.registration_form
        )

        if (
            self.template == backside_template or
            backside_template.backside_template or
            not same_size or
            not linked_to_same_regform
        ):
            raise BadRequest('Incompatible backside template')


class RHLinkDesignerTemplate(RHModifyDesignerTemplateBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.template,
            lambda self: self.regform
        }
    }

    def _process_args(self):
        RHModifyDesignerTemplateBase._process_args(self)
        regform_id = request.view_args['reg_form_id']
        self.regform = (RegistrationForm.query
                        .with_parent(self.template.event)
                        .filter_by(id=regform_id, is_deleted=False)
                        .first_or_404())

    def _process(self):
        if not can_link_to_regform(self.template, self.regform):
            raise BadRequest('Cannot link to the specified registration form.')

        self.template.link_regform(self.regform)
        self.template.event.log(EventLogRealm.event, LogKind.positive, 'Designer',
                                'Badge template linked to registration form', session.user,
                                data={'Template': self.template.title, 'Registration Form': self.regform.title})
        flash(_('Template successfully linked.'), 'success')
        return jsonify_data(html=_render_template_list(self.target, event=self.event_or_none))


class RHUnlinkDesignerTemplate(RHModifyDesignerTemplateBase):
    def _process(self):
        regform = self.template.registration_form
        if not regform:
            raise BadRequest('This template is not linked to any registration form.')
        if not self.template.is_unlinkable:
            raise BadRequest('This template cannot be unlinked because it contains '
                             'placeholders referencing the linked registration form.')

        self.template.unlink_regform()
        self.template.event.log(EventLogRealm.event, LogKind.negative, 'Designer',
                                'Badge template unlinked from registration form', session.user,
                                data={'Template': self.template.title, 'Registration Form': regform.title})
        flash(_('Template successfully unlinked.'), 'success')
        return jsonify_data(html=_render_template_list(self.target, event=self.event_or_none))


class RHDownloadTemplateImage(BacksideTemplateProtectionMixin, RHModifyDesignerTemplateBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.image
        }
    }

    def _process_args(self):
        RHModifyDesignerTemplateBase._process_args(self)
        self.image = DesignerImageFile.query.filter_by(id=request.view_args['image_id'], template=self.template).first()

    def _process(self):
        return self.image.send()


class RHUploadBackgroundImage(RHModifyDesignerTemplateBase):
    @use_kwargs({'background': fields.Bool(load_default=False)}, location='query')
    def _process(self, background):
        f = request.files['file']
        filename = secure_filename(f.filename, 'image')
        data = BytesIO()
        shutil.copyfileobj(f, data)
        data.seek(0)
        try:
            image_type = Image.open(data).format.lower()
        except OSError:
            # Invalid image data
            return jsonify(error='Invalid image data!')
        data.seek(0)
        if image_type not in {'jpeg', 'gif', 'png'}:
            return jsonify(error='File format not accepted!')
        content_type = 'image/' + image_type
        image = DesignerImageFile(template=self.template, filename=filename, content_type=content_type)
        if background:
            self.template.background_image = image
        image.save(data)
        flash(_('The image has been uploaded'), 'success')
        return jsonify_data(image_id=image.id, image_url=image.download_url)


class RHDeleteDesignerTemplate(RHModifyDesignerTemplateBase):
    def _process(self):
        db.session.delete(self.template)
        root = Category.get_root()
        # if we deleted the root category's default templates, pick
        # a system template as the new default (this always exists)
        if not root.default_ticket_template:
            system_templates = DesignerTemplate.query.filter(DesignerTemplate.is_system_template,
                                                             DesignerTemplate.type == TemplateType.badge).all()
            system_template = next(tpl for tpl in system_templates if tpl.is_ticket)
            root.default_ticket_template = system_template
        if not root.default_badge_template:
            system_templates = DesignerTemplate.query.filter(DesignerTemplate.is_system_template,
                                                             DesignerTemplate.type == TemplateType.badge).all()
            system_template = next(tpl for tpl in system_templates if not tpl.is_ticket)
            root.default_badge_template = system_template
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


class RHGetTemplateData(BacksideTemplateProtectionMixin, RHModifyDesignerTemplateBase):
    def _process(self):
        template_data = {
            'title': self.template.title,
            'data': self.template.data,
            'background_url': self.template.background_image.download_url if self.template.background_image else None,
            'images': {img.id: img.download_url for img in self.template.images} if self.template.images else None
        }
        return jsonify(template=template_data, backside_template_id=self.template.id)


class RHToggleTicketDefaultOnCategory(RHManageCategoryBase):
    def _process(self):
        template = DesignerTemplate.get_or_404(request.view_args['template_id'])
        all_ticket_templates = [tpl for tpl in get_all_templates(self.category)
                                if tpl.type == TemplateType.badge and tpl.is_ticket]
        if template not in all_ticket_templates:
            raise Exception('Invalid template')
        if template == self.category.default_ticket_template:
            # already the default -> clear it
            self.category.default_ticket_template = None
        elif template == get_default_ticket_on_category(self.category, only_inherited=True):
            # already the inherited default -> clear it instead of setting it explicitly
            self.category.default_ticket_template = None
        else:
            self.category.default_ticket_template = template
        if self.category.is_root and not self.category.default_ticket_template:
            raise Exception('Cannot clear default ticket template on root category')
        return jsonify_data(html=_render_template_list(self.category))


class RHToggleBadgeDefaultOnCategory(RHManageCategoryBase):
    def _process(self):
        template = DesignerTemplate.get_or_404(request.view_args['template_id'])
        all_badge_templates = [tpl for tpl in get_all_templates(self.category)
                               if tpl.type == TemplateType.badge and not tpl.is_ticket]
        if template not in all_badge_templates:
            raise Exception('Invalid template')
        if template == self.category.default_badge_template:
            # already the default -> clear it
            self.category.default_badge_template = None
        elif template == get_default_badge_on_category(self.category, only_inherited=True):
            # already the inherited default -> clear it instead of setting it explicitly
            self.category.default_badge_template = None
        else:
            self.category.default_badge_template = template
        if self.category.is_root and not self.category.default_badge_template:
            raise Exception('Cannot clear default ticket template on root category')
        return jsonify_data(html=_render_template_list(self.category))
