# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re

from flask import jsonify, request, session
from marshmallow import fields, validate
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.admin.controllers.base import RHAdminBase
from indico.modules.categories.controllers.management import RHManageCategoryBase
from indico.modules.categories.models.categories import Category
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.models.events import Event
from indico.modules.receipts.models.templates import ReceiptTemplate
from indico.modules.receipts.schemas import ReceiptTemplateSchema, ReceiptTplMetadataSchema
from indico.modules.receipts.util import compile_jinja_code, create_pdf, get_inherited_templates
from indico.modules.receipts.views import WPCategoryReceiptTemplates, WPEventReceiptTemplates
from indico.util.marshmallow import YAML
from indico.web.args import use_kwargs
from indico.web.flask.util import send_file


TITLE_ENUM_RE = re.compile(r'^(.*) \((\d+)\)$')


class ReceiptAreaMixin:
    """Basic class for all receitp template mixins.

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
        if not session.user or not session.user.is_admin:
            raise Forbidden


class ReceiptTemplateMixin(ReceiptAreaMixin):
    def _process_args(self):
        self.template = ReceiptTemplate.get_or_404(request.view_args['template_id'])


class ReceiptAreaRenderMixin(ReceiptAreaMixin):
    def _render_template(self, tpl_name, **kwargs):
        view_class = WPEventReceiptTemplates if self.object_type == 'event' else WPCategoryReceiptTemplates
        return view_class.render_template(tpl_name, self.target, 'receipts', target=self.target, **kwargs)


class TemplateListMixin(ReceiptAreaRenderMixin):
    def _process(self):
        inherited_templates = ReceiptTemplateSchema(many=True).dump(get_inherited_templates(self.target))
        own_templates = ReceiptTemplateSchema(many=True).dump(self.target.receipt_templates)
        return self._render_template(
            'list.html',
            inherited_templates=inherited_templates,
            own_templates=own_templates,
            target_locator=self.target.locator
        )


class RHListEventTemplates(TemplateListMixin, RHManageEventBase):
    pass


class RHListCategoryTemplates(TemplateListMixin, RHManageCategoryBase):
    pass


class RHAddTemplate(ReceiptAreaRenderMixin, RHAdminBase):
    always_clonable = False

    @use_kwargs({
        'title': fields.String(required=True, validate=validate.Length(3)),
        'html': fields.String(required=True, validate=validate.Length(3)),
        'css': fields.String(load_default=''),
        'yaml': YAML(ReceiptTplMetadataSchema, load_default=None)
    })
    def _process_POST(self, title, html, css, yaml):
        if yaml is None:
            yaml = {'custom_fields': []}
        template = ReceiptTemplate(title=title, html=html, css=css, custom_fields=yaml['custom_fields'],
                                   **self.target_dict)
        db.session.flush()
        return jsonify(ReceiptTemplateSchema().dump(template))


class DisplayTemplateMixin(ReceiptAreaRenderMixin):
    def _process(self):
        inherited_templates = ReceiptTemplateSchema(many=True).dump(get_inherited_templates(self.target))
        own_templates = ReceiptTemplateSchema(many=True).dump(self.target.receipt_templates)
        return self._render_template(
            'list.html',
            inherited_templates=inherited_templates,
            own_templates=own_templates,
            target_locator=self.target.locator
        )


class RHEventTemplate(DisplayTemplateMixin, RHManageEventBase):
    pass


class RHCategoryTemplate(DisplayTemplateMixin, RHManageCategoryBase):
    pass


class RHDeleteTemplate(ReceiptTemplateMixin, RHAdminBase):
    def _process(self):
        db.session.delete(self.template)


class RHEditTemplate(ReceiptTemplateMixin, RHAdminBase):
    @use_kwargs({
        'title': fields.String(validate=validate.Length(3)),
        'html': fields.String(validate=validate.Length(3)),
        'css': fields.String(),
        'yaml': YAML(ReceiptTplMetadataSchema, allow_none=True)
    })
    def _process(self, **data):
        yaml = data.pop('yaml', None)
        for key, value in data.items():
            setattr(self.template, key, value)

        self.template.custom_fields = yaml['custom_fields'] if yaml else []


class RHPreviewTemplate(ReceiptTemplateMixin, RHAdminBase):
    def _process(self):
        # XXX: correctly set registration, events, etc... to "dummy" values
        html = compile_jinja_code(
            self.template.html,
            custom_fields={f['name']: f.get('default') for f in self.template.custom_fields},
            event=self.target,
            registration=None
        )
        f = create_pdf(self.target, html, self.template.css)
        return send_file('receipt.pdf', f, 'application/pdf')


class RHCloneTemplate(ReceiptTemplateMixin, RHAdminBase):
    def _process(self, **data):
        base_title = self.template.title
        max_index = 0

        # this block will take care of adding `(N)` in front of each cloned title
        # extract out "base" portion of the title
        if m := TITLE_ENUM_RE.match(base_title):
            base_title = m.group(1)
            max_index = int(m.group(2))

        # look for all occurrences which start with the same "base title"
        matches = {tpl for tpl in self.target.receipt_templates if tpl.title.startswith(base_title)}
        # if we're cloning an inherited template, we don't need to exclude it from the matches (it's not there anyway)
        if self.target == self.template.owner:
            matches.remove(self.template)

        # figure out which has the highest "index" (the number between parenthesis)
        for match in matches:
            if m := TITLE_ENUM_RE.match(match.title):
                index = int(m.group(2))
                if index > max_index:
                    max_index = index

        new_title = f'{base_title} ({max_index + 1})' if max_index else f'{base_title} (1)'

        new_tpl = ReceiptTemplate(
            title=new_title,
            html=self.template.html,
            css=self.template.css,
            custom_fields=self.template.custom_fields,
            **self.target_dict
        )
        db.session.add(new_tpl)
        db.session.flush()
        return jsonify(ReceiptTemplateSchema().dump(new_tpl))
