# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import base64
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO

from flask import g, jsonify, request, session
from marshmallow import fields, validate
from pypdf import PdfWriter
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.admin.controllers.base import RHAdminBase
from indico.modules.categories.controllers.management import RHManageCategoryBase
from indico.modules.categories.models.categories import Category
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.models.events import Event
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.registration.notifications import notify_registration_receipt_created
from indico.modules.events.util import ZipGeneratorMixin
from indico.modules.files.models.files import File
from indico.modules.logs.models.entries import LogKind
from indico.modules.receipts.models.files import ReceiptFile
from indico.modules.receipts.models.templates import ReceiptTemplate
from indico.modules.receipts.schemas import (ReceiptTemplateAPISchema, ReceiptTemplateDBSchema,
                                             ReceiptTplMetadataSchema, TemplateDataSchema)
from indico.modules.receipts.util import (compile_jinja_code, create_pdf, get_inherited_templates,
                                          get_useful_registration_data)
from indico.modules.receipts.views import WPCategoryReceiptTemplates, WPEventReceiptTemplates
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.util.marshmallow import YAML, ModelList, not_empty
from indico.util.string import slugify
from indico.web.args import use_args, use_kwargs
from indico.web.flask.util import send_file


TITLE_ENUM_RE = re.compile(r'^(.*) \((\d+)\)$')


def _get_default_value(field):
    if field['type'] == 'dropdown' and 'default' in field['attributes']:
        return field['attributes']['options'][field['attributes']['default']]
    return field['attributes'].get('value')


def _generate_dummy_data(event: Event, custom_fields: dict):
    """Generate some dummy data to be used as an example."""
    return {
        'custom_fields': {f['name']: _get_default_value(f) for f in custom_fields},
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
            'section_title': _('Extras'),
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
    undefined: set[str] = field(default_factory=set)


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
        if not session.user or not session.user.is_admin:
            raise Forbidden


class ReceiptTemplateMixin(ReceiptAreaMixin):
    def _process_args(self):
        self.template = ReceiptTemplate.get_or_404(request.view_args['template_id'], is_deleted=False)


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
    def _process(self):
        schema = ReceiptTemplateDBSchema(only=('id', 'title', 'custom_fields', 'default_filename'), many=True)
        inherited_templates = schema.dump(get_inherited_templates(self.target))
        own_templates = schema.dump(self.target.receipt_templates)
        return jsonify(inherited_templates + own_templates)


class RHListEventTemplates(TemplateListMixin, RHManageEventBase):
    pass


class RHListCategoryTemplates(TemplateListMixin, RHManageCategoryBase):
    pass


class RHAddTemplate(ReceiptAreaRenderMixin, RHAdminBase):
    always_clonable = False

    @use_kwargs(ReceiptTemplateAPISchema)
    def _process(self, title, default_filename, html, css, yaml):
        if yaml is None:
            yaml = {'custom_fields': []}
        template = ReceiptTemplate(title=title, html=html, css=css, custom_fields=yaml['custom_fields'],
                                   default_filename=default_filename, **self.target_dict)
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
        self.template.is_deleted = True
        self.template.log(self.template.log_realm, LogKind.negative, 'Templates',
                          f'Document template "{self.template.title}" deleted', user=session.user)


class RHEditTemplate(ReceiptTemplateMixin, RHAdminBase):
    @use_args(ReceiptTemplateAPISchema)
    def _process(self, data):
        yaml = data.pop('yaml', None)
        for key, value in data.items():
            setattr(self.template, key, value)
        self.template.custom_fields = yaml['custom_fields'] if yaml else []
        self.template.log(self.template.log_realm, LogKind.change, 'Templates',
                          f'Document template "{self.template.title}" updated', user=session.user)


class RHAllEventTemplates(AllTemplateMixin, RHManageEventBase):
    pass


class RHAllCategoryTemplates(AllTemplateMixin, RHManageCategoryBase):
    pass


class RHPreviewTemplate(ReceiptTemplateMixin, RHAdminBase):
    def _process(self):
        # Just some dummy data to test the template
        html = compile_jinja_code(
            self.template.html,
            **_generate_dummy_data(self.target, self.template.custom_fields)
        )
        pdf_data = create_pdf(self.target, [html], self.template.css)
        return send_file('receipt.pdf', pdf_data, 'application/pdf')


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
        dummy_data = _generate_dummy_data(self.target, yaml.get('custom_fields', []) if yaml else [])
        compiled_html = compile_jinja_code(
            html,
            use_stack=True,
            **dummy_data
        )
        pdf_data = create_pdf(self.target, [compiled_html], css)
        return jsonify({
            'pdf': base64.b64encode(pdf_data.getvalue()),
            'data': TemplateDataSchema().dump(dummy_data)
        })


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
        del g.template_stack
        pdf_data = create_pdf(self.target, html_sources, self.template.css)
        return jsonify({'pdf': base64.b64encode(pdf_data.getvalue())})


class RHGenerateReceipts(ReceiptTemplateMixin, RHManageEventBase):
    @use_kwargs({
        'registration_ids': fields.List(fields.Integer(), required=True),
        'custom_fields': fields.Dict(keys=fields.String, load_default={}),
        'filename': fields.String(required=True, validate=not_empty),
        'publish': fields.Bool(load_default=False),
        'notify_users': fields.Bool(load_default=False),
        'force': fields.Bool(load_default=False)
    })
    def _process(self, registration_ids, custom_fields, filename, publish, notify_users, force):
        # fetch corresponding Registration objects, among those belonging to the event
        registrations = Registration.query.filter(
            Registration.id.in_(registration_ids), RegistrationForm.event == self.target
        ).join(RegistrationForm, Registration.registration_form_id == RegistrationForm.id)

        def _compile_receipt_for_reg(registration):
            g.template_stack.append(TemplateStackEntry(registration))
            return compile_jinja_code(
                self.template.html,
                use_stack=True,
                custom_fields={f['name']: custom_fields.get(f['name']) for f in self.template.custom_fields},
                event=self.target,
                **get_useful_registration_data(registration.registration_form, registration)
            )

        g.template_stack = []
        html_sources = {registration: _compile_receipt_for_reg(registration) for registration in registrations}

        errors = [
            {
                'registration': {'full_name': entry.registration.display_full_name, 'id': entry.registration.id},
                'undefineds': list(entry.undefined)
            }
            for entry in g.template_stack if entry.undefined
        ]
        del g.template_stack
        if errors and not force:
            return jsonify(receipt_ids=[], errors=errors)

        receipt_ids = []
        for registration in registrations:
            pdf_content = create_pdf(self.target, [html_sources[registration]], self.template.css)
            timestamp = datetime.now().strftime('%Y%m%d-%H%M')
            full_filename = slugify(filename, timestamp)
            n = (ReceiptFile.query
                 .join(File)
                 .filter(ReceiptFile.registration == registration, File.filename.like(f'{full_filename}%.pdf'))
                 .count())
            if n > 0:
                full_filename = f'{full_filename}-{n}'
            f = File(
                filename=secure_filename(f'{full_filename}.pdf', f'document-{timestamp}.pdf'),
                content_type='application/pdf',
                meta={'event_id': self.target.id}
            )
            context = ('event', self.target.id, 'registration', registration.id, 'receipts')
            f.save(context, pdf_content)
            receipt = ReceiptFile(
                file=f,
                registration=registration,
                template=self.template,
                template_params=custom_fields,
                is_published=publish
            )
            db.session.add(receipt)
            db.session.commit()
            receipt_ids.append(receipt.file_id)
            notify_registration_receipt_created(registration, receipt, notify_user=notify_users)
        return jsonify(receipt_ids=receipt_ids, errors=errors)


class RHCloneTemplate(ReceiptTemplateMixin, RHAdminBase):
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
            default_filename=self.template.default_filename,
            **self.target_dict
        )
        db.session.add(new_tpl)
        db.session.flush()
        new_tpl.log(new_tpl.log_realm, LogKind.positive, 'Templates', f'Document template "{new_tpl.title}" created',
                    user=session.user, data={'Cloned from': self.template.title})
        return jsonify(ReceiptTemplateDBSchema().dump(new_tpl))


class RHExportReceipts(RHManageEventBase, ZipGeneratorMixin):
    """Export an archive of multiple receipts."""

    def _prepare_folder_structure(self, file):
        registration = file.receipt_file.registration
        registrant_name = f'{registration.get_full_name()}_{registration.friendly_id}'
        file_name = secure_filename(f'{file.id}_{registrant_name}_{file.filename}', f'{file.id}_document')
        return os.path.join(*self._adjust_path_length([file_name]))

    def _iter_items(self, receipts):
        for receipt in receipts:
            yield receipt.file

    @use_kwargs({
        'receipts': ModelList(ReceiptFile, filter_deleted=True, data_key='receipt_ids', required=True,
                              validate=not_empty)
    })
    def _process(self, receipts):
        if request.view_args['format'] == 'zip':
            return self._generate_zip_file(receipts)
        output = PdfWriter()
        for receipt in receipts:
            with receipt.file.open() as fd:
                output.append(fd)
        outputbuf = BytesIO()
        output.write(outputbuf)
        outputbuf.seek(0)
        return send_file('documents.pdf', outputbuf, 'application/pdf')
