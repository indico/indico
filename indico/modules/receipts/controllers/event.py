# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import base64
import os
from datetime import datetime
from io import BytesIO

from flask import g, jsonify, request, session
from marshmallow import fields
from pypdf import PdfWriter
from webargs.flaskparser import abort
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.categories.models.categories import Category
from indico.modules.events.registration.controllers.management import RHManageRegFormsBase
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.registration.notifications import notify_registration_receipt_created
from indico.modules.events.util import ZipGeneratorMixin
from indico.modules.files.models.files import File
from indico.modules.logs.models.entries import EventLogRealm, LogKind
from indico.modules.receipts.models.files import ReceiptFile
from indico.modules.receipts.models.templates import ReceiptTemplate
from indico.modules.receipts.schemas import ReceiptTemplateDBSchema
from indico.modules.receipts.settings import receipt_defaults
from indico.modules.receipts.util import (TemplateStackEntry, compile_jinja_code, create_pdf, get_inherited_templates,
                                          get_safe_template_context)
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.util.marshmallow import not_empty
from indico.util.string import slugify
from indico.web.args import use_kwargs
from indico.web.flask.util import send_file


class RHAllEventTemplates(RHManageRegFormsBase):
    """Get all available receipt templates for an event."""

    def _apply_event_defaults(self, tpl, defaults):
        for field in tpl['custom_fields']:
            if (default := defaults.get(field['name'])) is None:
                continue
            if field['type'] == 'dropdown':
                try:
                    idx = field['attributes']['options'].index(default)
                except IndexError:
                    continue
                field['attributes']['default'] = idx
            else:
                field['attributes']['value'] = default

    def _process(self):
        schema = ReceiptTemplateDBSchema(only=('id', 'title', 'custom_fields', 'default_filename'), many=True)
        inherited_templates = schema.dump(get_inherited_templates(self.event))
        own_templates = schema.dump(self.event.receipt_templates)
        templates = sorted(inherited_templates + own_templates, key=lambda x: x['title'].lower())
        for tpl in templates:
            if defaults := receipt_defaults.get(self.event, f"custom_fields:{tpl['id']}"):
                self._apply_event_defaults(tpl, defaults)
            if filename := receipt_defaults.get(self.event, f"filename:{tpl['id']}"):
                tpl['default_filename'] = filename
        return jsonify(templates)


class EventReceiptTemplateMixin:
    """Mixin to require event management permissions for a receipt template."""

    def _process_args(self):
        self.template = ReceiptTemplate.get_or_404(request.view_args['template_id'], is_deleted=False)

    def _check_access(self):
        # Check that template belongs to this event or a category that is a parent
        if self.template.owner == self.event:
            return
        valid_category_ids = self.event.category_chain or [Category.get_root().id]
        if self.template.owner.id not in valid_category_ids:
            raise Forbidden


class RenderReceiptsBase(EventReceiptTemplateMixin, RHManageRegFormsBase):
    @use_kwargs({
        'registration_ids': fields.List(fields.Integer(), required=True),
        'custom_fields': fields.Dict(keys=fields.String, load_default=lambda: {}),
    })
    def _process_args(self, registration_ids, custom_fields):
        RHManageRegFormsBase._process_args(self)
        EventReceiptTemplateMixin._process_args(self)
        self.registrations = (Registration.query
                              .filter(Registration.id.in_(registration_ids),
                                      RegistrationForm.event == self.event)
                              .join(RegistrationForm, Registration.registration_form_id == RegistrationForm.id)
                              .all())
        self.custom_fields_raw = custom_fields

    def _check_access(self):
        RHManageRegFormsBase._check_access(self)
        EventReceiptTemplateMixin._check_access(self)

    def _get_custom_fields(self):
        custom_fields = {f['name']: self.custom_fields_raw.get(f['name']) for f in self.template.custom_fields}
        missing = [f['attributes']['label'] for f in self.template.custom_fields
                   if not custom_fields[f['name']] and f.get('validations', {}).get('required')]
        if missing:
            abort(422, messages={'custom_fields': [_('Required fields missing: {}').format(', '.join(missing))]})
        return custom_fields


class RHPreviewReceipts(RenderReceiptsBase):
    """Preview receipt PDFs for selected registrations."""

    def _process(self):
        custom_fields = self._get_custom_fields()
        g.template_stack = []
        html_sources = []
        for registration in self.registrations:
            g.template_stack.append(TemplateStackEntry(registration))
            safe_ctx = get_safe_template_context(self.event, registration, custom_fields)
            html_sources.append(compile_jinja_code(self.template.html, safe_ctx, use_stack=True))
        del g.template_stack
        pdf_data = create_pdf(self.event, html_sources, self.template.css)
        return jsonify({'pdf': base64.b64encode(pdf_data.getvalue())})


class RHGenerateReceipts(RenderReceiptsBase):
    """Generate (and save) receipts PDFs for selected registrations."""

    @use_kwargs({
        'save_config': fields.Bool(load_default=False),
        'filename': fields.String(required=True, validate=not_empty),
        'publish': fields.Bool(load_default=False),
        'notify_users': fields.Bool(load_default=False),
        'force': fields.Bool(load_default=False)
    })
    def _process(self, save_config, filename, publish, notify_users, force):
        custom_fields = self._get_custom_fields()

        def _compile_receipt_for_reg(registration):
            g.template_stack.append(TemplateStackEntry(registration))
            safe_ctx = get_safe_template_context(self.event, registration, custom_fields)
            return compile_jinja_code(self.template.html, safe_ctx, use_stack=True)

        g.template_stack = []
        html_sources = {registration: _compile_receipt_for_reg(registration) for registration in self.registrations}

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
        for registration in self.registrations:
            pdf_content = create_pdf(self.event, [html_sources[registration]], self.template.css)
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
                meta={'event_id': self.event.id}
            )
            context = ('event', self.event.id, 'registration', registration.id, 'receipts')
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
            registration.log(EventLogRealm.management, LogKind.positive, 'Documents',
                             f'Document "{f.filename}" generated', session.user,
                             data={'Published': publish, 'Notified': notify_users})
        if save_config:
            receipt_defaults.set_multi(self.event, {
                f'custom_fields:{self.template.id}': self.custom_fields_raw,
                f'filename:{self.template.id}': filename,
            })
        return jsonify(receipt_ids=receipt_ids, errors=errors)


class RHExportReceipts(ZipGeneratorMixin, RHManageRegFormsBase):
    """Export an archive of multiple receipts."""

    def _prepare_folder_structure(self, file):
        reg = file.receipt_file.registration
        registrant_name = f'{reg.get_full_name()}_{reg.friendly_id}'
        file_name = secure_filename(f'{registrant_name}_{file.id}_{file.filename}', f'{file.id}_document.pdf')
        return os.path.join(*self._adjust_path_length([file_name]))

    def _iter_items(self, receipts):
        for receipt in receipts:
            yield receipt.file

    @use_kwargs({
        'receipt_ids': fields.List(fields.Integer(), required=True, validate=not_empty),
    })
    def _process_args(self, receipt_ids):
        RHManageRegFormsBase._process_args(self)
        self.receipts = (ReceiptFile.query
                         .filter(ReceiptFile.file_id.in_(receipt_ids),
                                 ReceiptFile.registration.has(event=self.event),
                                 ~ReceiptFile.is_deleted)
                         .all())

    def _process(self):
        if request.view_args['format'] == 'zip':
            return self._generate_zip_file(self.receipts)
        output = PdfWriter()
        for receipt in self.receipts:
            with receipt.file.open() as fd:
                output.append(fd)
        outputbuf = BytesIO()
        output.write(outputbuf)
        outputbuf.seek(0)
        return send_file('documents.pdf', outputbuf, 'application/pdf')
