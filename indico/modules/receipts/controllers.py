# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
import typing as t
from dataclasses import dataclass, field

from flask import g, json, jsonify, request, session
from marshmallow import fields, validate
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.admin.controllers.base import RHAdminBase
from indico.modules.categories.controllers.management import RHManageCategoryBase
from indico.modules.categories.models.categories import Category
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.models.events import Event
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.files.models.files import File
from indico.modules.receipts.models.files import ReceiptFile
from indico.modules.receipts.models.templates import ReceiptTemplate
from indico.modules.receipts.schemas import (ReceiptTemplateAPISchema, ReceiptTemplateDBSchema,
                                             ReceiptTplMetadataSchema, TemplateDataSchema)
from indico.modules.receipts.util import (compile_jinja_code, create_pdf, get_inherited_templates,
                                          get_useful_registration_data)
from indico.modules.receipts.views import WPCategoryReceiptTemplates, WPEventReceiptTemplates
from indico.util.i18n import _
from indico.util.marshmallow import YAML
from indico.web.args import use_kwargs
from indico.web.flask.util import send_file


TITLE_ENUM_RE = re.compile(r'^(.*) \((\d+)\)$')


def generate_dummy_data(event: Event, custom_fields: dict):
    """Generate some dummy data to be used as an example."""
    return {
        'custom_fields': {f['name']: f.get('default') for f in (custom_fields)},
        'event': event,
        'personal_data': {
            'title': 'Dr',
            'first_name': 'John',
            'last_name': 'Doe',
            'affiliation': 'Atlantis Institute  ',
            'position': 'Unicorn Specialist',
            'address': '123 Route des Licornes',
            'country': 'France',
            'email': 'john.doe@example.com',
            'price': 100
        },
        'fields': [{
            'title': _('Social Dinner'),
            'value': True,
            'field_data': {
                'price': 50
            },
            'actual_price': 50
        }],
        'base_price': 50,
        'total_price': 100,
        'currency': 'EUR',
        'formatted_price': '100 EUR'
    }


@dataclass
class TemplateStackEntry:
    registration: Registration
    undefined: t.Set[str] = field(default_factory=set)


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
        inherited_templates = ReceiptTemplateDBSchema(many=True).dump(get_inherited_templates(self.target))
        own_templates = ReceiptTemplateDBSchema(many=True).dump(self.target.receipt_templates)
        return self._render_template(
            'list.html',
            inherited_templates=inherited_templates,
            own_templates=own_templates,
            target_locator=self.target.locator
        )


class AllTemplateMixin(ReceiptAreaMixin):
    def _process(self, **data):
        inherited_templates = ReceiptTemplateDBSchema(many=True).dump(get_inherited_templates(self.target))
        own_templates = ReceiptTemplateDBSchema(many=True).dump(self.target.receipt_templates)
        return jsonify(inherited_templates + own_templates)


class RHListEventTemplates(TemplateListMixin, RHManageEventBase):
    pass


class RHListCategoryTemplates(TemplateListMixin, RHManageCategoryBase):
    pass


class RHAddTemplate(ReceiptAreaRenderMixin, RHAdminBase):
    always_clonable = False

    @use_kwargs(ReceiptTemplateAPISchema)
    def _process(self, title, type, html, css, yaml):
        if yaml is None:
            yaml = {'custom_fields': []}
        template = ReceiptTemplate(type=type, title=title, html=html, css=css, custom_fields=yaml['custom_fields'],
                                   **self.target_dict)
        db.session.flush()
        return jsonify(ReceiptTemplateDBSchema().dump(template))


class DisplayTemplateMixin(ReceiptAreaRenderMixin):
    def _process(self):
        inherited_templates = ReceiptTemplateDBSchema(many=True).dump(get_inherited_templates(self.target))
        own_templates = ReceiptTemplateDBSchema(many=True).dump(self.target.receipt_templates)
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
    @use_kwargs(ReceiptTemplateAPISchema)
    def _process(self, **data):
        yaml = data.pop('yaml', None)
        for key, value in data.items():
            setattr(self.template, key, value)

        self.template.custom_fields = yaml['custom_fields'] if yaml else []


class RHAllEventTemplates(AllTemplateMixin, RHManageEventBase):
    pass


class RHAllCategoryTemplates(AllTemplateMixin, RHManageCategoryBase):
    pass


class RHGetDummyData(ReceiptAreaMixin, RHAdminBase):
    @use_kwargs({
        'template_id': fields.Integer(load_default=None)
    }, location='query')
    def _process(self, template_id):
        if template_id:
            template = ReceiptTemplate.get_or_404(template_id)
            custom_fields = template.custom_fields
        else:
            custom_fields = {}
        return jsonify(TemplateDataSchema().dump(generate_dummy_data(self.target, custom_fields)))


class RHPreviewTemplate(ReceiptTemplateMixin, RHAdminBase):
    def _process(self):
        # Just some dummy data to test the template
        html = compile_jinja_code(
            self.template.html,
            **generate_dummy_data(self.target, self.template.custom_fields)
        )
        f = create_pdf(self.target, {html}, self.template.css)

        return send_file('receipt.pdf', f, 'application/pdf')


class RHLivePreview(ReceiptAreaMixin, RHAdminBase):
    DENY_FRAMES = False

    @use_kwargs({
        'html': fields.String(required=True, validate=validate.Length(3)),
        'css': fields.String(load_default=''),
        'yaml': YAML(ReceiptTplMetadataSchema, load_default=None, allow_none=True),
    })
    def _process(self, html, css, yaml):
        g.template_stack = [TemplateStackEntry(None)]
        # Just some dummy data to test the template
        compiled_html = compile_jinja_code(
            html,
            use_stack=True,
            **generate_dummy_data(self.target, yaml.get('custom_fields', []) if yaml else [])
        )
        return send_file('receipt.pdf', create_pdf(self.target, {compiled_html}, css), 'application/pdf')


class RHPreviewReceipts(ReceiptTemplateMixin, RHManageEventBase):
    @use_kwargs({
        'registration_ids': fields.List(fields.Integer()),
        'custom_fields': fields.Dict(keys=fields.String)
    })
    def _process(self, registration_ids=None, custom_fields=None):
        # fetch corresponding Registration objects, among those belonging to the event
        registrations = Registration.query.filter(
            Registration.id.in_(registration_ids), RegistrationForm.event == self.target
        ).join(RegistrationForm, Registration.registration_form_id == RegistrationForm.id)

        g.template_stack = []
        html_sources = []
        for registration in registrations:
            g.template_stack.append(TemplateStackEntry(registration))
            html_sources.append(compile_jinja_code(
                self.template.html,
                use_stack=True,
                custom_fields={f['name']: custom_fields.get(f['name']) for f in self.template.custom_fields},
                event=self.target,
                **get_useful_registration_data(registration.registration_form, registration)
            ))
        #TODO add preview watermark

        response = send_file(
            'receipt.pdf', create_pdf(self.target, html_sources, self.template.css), 'application/pdf'
        )
        undefineds = [
            {
                'registration': dict(entry.registration.get_personal_data(), id=entry.registration.id),
                'undefineds': list(entry.undefined)
            }
            for entry in g.template_stack if entry.undefined
        ]
        if undefineds:
            response.headers['X-Indico-Template-Errors'] = json.dumps(undefineds)
        del g.template_stack
        return response


class RHGenerateReceipts(ReceiptTemplateMixin, RHManageEventBase):
    @use_kwargs({
        'registration_ids': fields.List(fields.Integer()),
        'notify_email': fields.Bool(load_default=True), # TODO move this to PublishReceipt
        'custom_fields': fields.Dict(keys=fields.String)
    })
    def _process(self, registration_ids=None, notify_email=None, custom_fields=None):
        # fetch corresponding Registration objects, among those belonging to the event
        registrations = Registration.query.filter(
            Registration.id.in_(registration_ids), RegistrationForm.event == self.target
        ).join(RegistrationForm, Registration.registration_form_id == RegistrationForm.id)

        g.template_stack = []
        for registration in registrations:
            g.template_stack.append(TemplateStackEntry(registration))
            html_source = compile_jinja_code(
                self.template.html,
                use_stack=True,
                custom_fields={f['name']: custom_fields.get(f['name']) for f in self.template.custom_fields},
                event=self.target,
                **get_useful_registration_data(registration.registration_form, registration)
            )
            pdf_content = create_pdf(self.target, {html_source}, self.template.css)
            n = ReceiptFile.query.filter(ReceiptFile.registration == registration,
                                         ReceiptFile.template.has(type=self.template.type)).count()
            f = File(
                filename=f'{self.template.type.file_prefix}-{n + 1}.pdf',
                content_type='application/pdf',
                meta={'event_id': self.target.id}
            )
            context = ('event', self.target.id, 'registration', registration.id, 'receipts')
            f.save(context, pdf_content)
            rf = ReceiptFile(
                file=f,
                registration=registration,
                template=self.template,
                template_params=custom_fields
            )
            db.session.add(rf)
            db.session.commit()

        undefineds = [
            {
                'registration': dict(entry.registration.get_personal_data(), id=entry.registration.id),
                'undefineds': list(entry.undefined)
            }
            for entry in g.template_stack if entry.undefined
        ]
        if undefineds:
            #TODO figure out what to do with errors. maybe log them somewhere?
            #response.headers['X-Indico-Template-Errors'] = json.dumps(undefineds)
            pass
        del g.template_stack

        return '', 204


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
            type=self.template.type,
            title=new_title,
            html=self.template.html,
            css=self.template.css,
            custom_fields=self.template.custom_fields,
            **self.target_dict
        )
        db.session.add(new_tpl)
        db.session.flush()
        return jsonify(ReceiptTemplateDBSchema().dump(new_tpl))
