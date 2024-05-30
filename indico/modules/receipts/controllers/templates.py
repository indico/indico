# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import base64
import re
from pathlib import Path

import yaml
from flask import current_app, g, jsonify, request, session
from marshmallow import fields, validate
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.db import db
from indico.modules.categories.controllers.management import RHManageCategoryBase
from indico.modules.categories.models.categories import Category
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.models.events import Event
from indico.modules.events.util import check_event_locked
from indico.modules.logs.models.entries import LogKind
from indico.modules.logs.util import make_diff_log
from indico.modules.receipts.models.templates import ReceiptTemplate
from indico.modules.receipts.schemas import ReceiptTemplateAPISchema, ReceiptTemplateDBSchema, ReceiptTplMetadataSchema
from indico.modules.receipts.util import (TemplateStackEntry, can_user_manage_receipt_templates, compile_jinja_code,
                                          create_pdf, get_dummy_preview_data, get_inherited_templates,
                                          get_other_templates, get_preview_placeholders)
from indico.modules.receipts.views import WPCategoryReceiptTemplates, WPEventReceiptTemplates
from indico.util.marshmallow import YAML
from indico.web.args import use_args, use_kwargs
from indico.web.flask.util import send_file
from indico.web.rh import RHProtected


TITLE_ENUM_RE = re.compile(r'^(.*) \((\d+)\)$')


def _get_default_templates_dir():
    return Path(current_app.root_path) / 'modules' / 'receipts' / 'default_templates'


class ReceiptAreaMixin:
    """Basic class for all receipt template mixins.

    It resolves the target object type from the blueprint URL.
    """

    @property
    def object_type(self):
        """Figure out whether we're targetting an event or category, based on URL info."""
        return request.view_args['object_type']

    @property
    def target_dict(self):
        return {'event': self.target} if self.object_type == 'event' else {'category': self.target}

    @property
    def target(self):
        event_id = request.view_args.get('event_id')
        categ_id = request.view_args.get('category_id')
        return Event.get_or_404(event_id) if self.object_type == 'event' else Category.get_or_404(categ_id)

    def _check_access(self):
        # General access check to manage receipt templates (admin or on explicit ACL)
        if not can_user_manage_receipt_templates(session.user):
            raise Forbidden
        # Event/category-level access check (important if user is not an admin)
        if not self.target.can_manage(session.user):
            raise Forbidden
        elif isinstance(self.target, Event):
            check_event_locked(self, self.target)


class ReceiptTemplateMixin(ReceiptAreaMixin):
    def _process_args(self):
        self.template = ReceiptTemplate.get_or_404(request.view_args['template_id'], is_deleted=False)

    def _check_access(self):
        ReceiptAreaMixin._check_access(self)
        # Check that template belongs to this event or a category that is a parent
        if self.template.owner == self.target:
            return
        # If the user can manage the template owner, no need to check further
        if self.template.owner.can_manage(session.user):
            return
        category_chain = self.target.chain_ids if isinstance(self.target, Category) else self.target.category_chain
        valid_category_ids = category_chain or [Category.get_root().id]
        if self.template.owner.id not in valid_category_ids:
            raise Forbidden


class TemplateListMixin(ReceiptAreaMixin):
    def _process(self):
        view_only_schema = ReceiptTemplateDBSchema(many=True, only={'id', 'title', 'owner'})
        inherited_templates = view_only_schema.dump(get_inherited_templates(self.target))
        other_templates = view_only_schema.dump(get_other_templates(self.target, session.user))
        own_templates = ReceiptTemplateDBSchema(many=True).dump(self.target.receipt_templates)
        default_templates_dir = _get_default_templates_dir()
        default_templates = {f.stem: yaml.safe_load(f.read_text()) for f in default_templates_dir.glob('*.yaml')}
        view_class = WPEventReceiptTemplates if self.object_type == 'event' else WPCategoryReceiptTemplates
        return view_class.render_template(
            'list.html', self.target, 'receipts',
            target=self.target,
            inherited_templates=inherited_templates,
            other_templates=other_templates,
            own_templates=own_templates,
            default_templates=default_templates,
            target_locator=self.target.locator
        )


class RHReceiptTemplatesManagementBase(RHProtected):
    DENY_FRAMES = True


class RHEventTemplatesManagement(TemplateListMixin, RHManageEventBase):
    """Display the template management page for an event."""


class RHCategoryTemplatesManagement(TemplateListMixin, RHManageCategoryBase):
    """Display the template management page for a category."""


class RHAddTemplate(ReceiptAreaMixin, RHReceiptTemplatesManagementBase):
    """Add a new template."""

    @use_kwargs(ReceiptTemplateAPISchema)
    def _process(self, title, default_filename, html, css, yaml):
        template = ReceiptTemplate(title=title, html=html, css=css, yaml=yaml,
                                   default_filename=default_filename, **self.target_dict)
        db.session.flush()
        template.log(template.log_realm, LogKind.positive, 'Templates',
                     f'Document template "{template.title}" created',
                     user=session.user, data={'HTML': html, 'CSS': css, 'YAML': yaml})
        return ReceiptTemplateDBSchema().jsonify(template)


class RHDeleteTemplate(ReceiptTemplateMixin, RHReceiptTemplatesManagementBase):
    """Delete a template."""

    def _process(self):
        self.template.is_deleted = True
        self.template.log(self.template.log_realm, LogKind.negative, 'Templates',
                          f'Document template "{self.template.title}" deleted', user=session.user)


class RHEditTemplate(ReceiptTemplateMixin, RHReceiptTemplatesManagementBase):
    """Update a template."""

    @use_args(ReceiptTemplateAPISchema)
    def _process(self, data):
        if changes := self.template.populate_from_dict(data):
            log_fields = {
                'title': {'title': 'Title', 'type': 'string'},
                'default_filename': {'title': 'Default filename', 'type': 'string'},
                'html': 'HTML',
                'css': 'CSS',
                'yaml': 'YAML',
            }
            self.template.log(self.template.log_realm, LogKind.change, 'Templates',
                              f'Document template "{self.template.title}" updated', user=session.user,
                              data={'Changes': make_diff_log(changes, log_fields)})


class RHPreviewTemplate(ReceiptTemplateMixin, RHReceiptTemplatesManagementBase):
    """Preview a template with dummy data."""

    def _process(self):
        # Just some dummy data to test the template
        html = compile_jinja_code(self.template.html, get_dummy_preview_data(self.template.custom_fields))
        pdf_data = create_pdf(self.target, [html], self.template.css)
        filename = self.template.default_filename or 'preview.pdf'
        return send_file(filename, pdf_data, 'application/pdf')


class RHLivePreview(ReceiptAreaMixin, RHReceiptTemplatesManagementBase):
    """Preview a template while editing it."""

    @use_kwargs({
        'html': fields.String(required=True, validate=validate.Length(3)),
        'css': fields.String(required=True),
        'yaml': YAML(ReceiptTplMetadataSchema, required=True),
        'custom_fields_values': fields.Dict(keys=fields.String, load_default=lambda: {}),
    })
    def _process(self, html, css, yaml, custom_fields_values):
        g.template_stack = [TemplateStackEntry(None)]
        # Just some dummy data to test the template
        custom_fields = yaml.get('custom_fields', [])
        dummy_data = get_dummy_preview_data(custom_fields, custom_fields_values)
        compiled_html = compile_jinja_code(html, dummy_data, use_stack=True)
        pdf_data = create_pdf(self.target, [compiled_html], css)
        return jsonify({
            'pdf': base64.b64encode(pdf_data.getvalue()),
            'data': get_preview_placeholders(dummy_data),
            'custom_fields': custom_fields,
        })


class RHCloneTemplate(ReceiptTemplateMixin, RHReceiptTemplatesManagementBase):
    """Clone a template into the current target location."""

    def _process(self):
        base_title = self.template.title
        max_index = 0

        # this block will take care of adding `(N)` in front of each cloned title
        # extract out "base" portion of the title
        if m := TITLE_ENUM_RE.match(base_title):
            base_title = m.group(1)
            max_index = int(m.group(2))

        # look for all occurrences which start with the same "base title"
        matches = {tpl for tpl in self.target.receipt_templates if tpl.title.startswith(base_title)}

        # figure out which has the highest "index" (the number between parenthesis)
        found = False
        for match in matches:
            if m := TITLE_ENUM_RE.match(match.title):
                found = True
                index = int(m.group(2))
                max_index = max(index, max_index)
            elif match.title == base_title:
                found = True

        if found:
            new_title = f'{base_title} ({max_index + 1})' if max_index else f'{base_title} (1)'
        else:
            # if we have no exact conflicts nor indexed titles, just keep the base title
            new_title = base_title

        new_tpl = ReceiptTemplate(
            title=new_title,
            html=self.template.html,
            css=self.template.css,
            yaml=self.template.yaml,
            default_filename=self.template.default_filename,
            **self.target_dict
        )
        db.session.add(new_tpl)
        db.session.flush()
        new_tpl.log(new_tpl.log_realm, LogKind.positive, 'Templates', f'Document template "{new_tpl.title}" created',
                    user=session.user, data={'Cloned from': self.template.title})
        return ReceiptTemplateDBSchema().jsonify(new_tpl)


class RHGetDefaultTemplate(RHProtected):
    """Get a template from a default template."""

    def _check_access(self):
        RHProtected._check_access(self)
        if not can_user_manage_receipt_templates(session.user):
            raise Forbidden

    def _process(self):
        name = request.view_args['template_name']
        default_templates_dir = _get_default_templates_dir()
        metadata_file = next((f for f in default_templates_dir.glob('*.yaml') if f.stem == name), None)
        if metadata_file is None:
            raise NotFound('Template does not exist')
        tpl_data = yaml.safe_load(metadata_file.read_text())
        tpl_data['title'] = f'{tpl_data["title"]} (v{tpl_data["version"]})'
        del tpl_data['version']
        template_dir = default_templates_dir / metadata_file.stem
        tpl_data['html'] = (template_dir / 'template.html').read_text()
        tpl_data['css'] = (template_dir / 'theme.css').read_text()
        tpl_data['yaml'] = (template_dir / 'metadata.yaml').read_text()
        return ReceiptTemplateAPISchema().jsonify(tpl_data)
