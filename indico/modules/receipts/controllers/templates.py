# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import base64
import re
from datetime import datetime

from flask import g, jsonify, request, session
from marshmallow import fields, validate
from pytz import utc
from werkzeug.exceptions import Forbidden

from indico.core.config import config
from indico.core.db import db
from indico.modules.categories.controllers.management import RHManageCategoryBase
from indico.modules.categories.models.categories import Category
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.models.events import Event, EventType
from indico.modules.events.util import check_event_locked
from indico.modules.logs.models.entries import LogKind
from indico.modules.logs.util import make_diff_log
from indico.modules.receipts.models.templates import ReceiptTemplate
from indico.modules.receipts.schemas import (ReceiptTemplateAPISchema, ReceiptTemplateDBSchema,
                                             ReceiptTplMetadataSchema, TemplateDataSchema)
from indico.modules.receipts.util import (TemplateStackEntry, can_user_manage_receipt_templates, compile_jinja_code,
                                          create_pdf, get_inherited_templates)
from indico.modules.receipts.views import WPCategoryReceiptTemplates, WPEventReceiptTemplates
from indico.util.i18n import _
from indico.util.marshmallow import YAML
from indico.web.args import use_args, use_kwargs
from indico.web.flask.util import send_file
from indico.web.rh import RHProtected


TITLE_ENUM_RE = re.compile(r'^(.*) \((\d+)\)$')


def _get_default_value(field):
    if field['type'] == 'dropdown' and 'default' in field['attributes']:
        return field['attributes']['options'][field['attributes']['default']]
    elif field['type'] == 'checkbox':
        return field['attributes'].get('value', False)
    return field['attributes'].get('value', '')


def _generate_dummy_data(custom_fields: dict):
    """Generate some dummy data to be used as an example."""
    fake_event = Event(
        id=42,
        category=Category.get_root(),
        _type=EventType.conference,
        title='How to build a Stargate',
        own_venue_name='University Campus',
        own_room_name='Main Auditorium',
        own_address='Science Road 1\nCH-1234 Switzerland',
        start_dt=datetime(2023, 12, 24, 16, tzinfo=utc),
        end_dt=datetime(2023, 12, 24, 20, tzinfo=utc),
        timezone=config.DEFAULT_TIMEZONE,
    )
    db.session.expunge(fake_event)  # setting a category adds it to the SA session
    assert fake_event not in db.session
    return {
        'custom_fields': {f['name']: _get_default_value(f) for f in custom_fields},
        'event': fake_event,
        'registration': {
            'id': 123456,
            'friendly_id': 42,
            'submitted_dt': datetime(2023, 12, 8, 12, 37, tzinfo=utc)
        },
        'registration_global_id': 123456,
        'registration_friendly_id': 42,
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
            'input_type': 'checkbox',
            'value': True,
            'friendly_value': 'Yes',
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
        category_chain = self.target.chain_ids if isinstance(self.target, Category) else self.target.category_chain
        valid_category_ids = category_chain or [Category.get_root().id]
        if self.template.owner.id not in valid_category_ids:
            raise Forbidden


class TemplateListMixin(ReceiptAreaMixin):
    def _process(self):
        inherited_templates = ReceiptTemplateDBSchema(many=True).dump(get_inherited_templates(self.target))
        own_templates = ReceiptTemplateDBSchema(many=True).dump(self.target.receipt_templates)
        view_class = WPEventReceiptTemplates if self.object_type == 'event' else WPCategoryReceiptTemplates
        return view_class.render_template(
            'list.html', self.target, 'receipts',
            target=self.target,
            inherited_templates=inherited_templates,
            own_templates=own_templates,
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
        return jsonify(ReceiptTemplateDBSchema().dump(template))


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
        html = compile_jinja_code(
            self.template.html,
            **_generate_dummy_data(self.template.custom_fields)
        )
        pdf_data = create_pdf(self.target, [html], self.template.css)
        return send_file('receipt.pdf', pdf_data, 'application/pdf')


class RHLivePreview(ReceiptAreaMixin, RHReceiptTemplatesManagementBase):
    """Preview a template while editing it."""

    @use_kwargs({
        'html': fields.String(required=True, validate=validate.Length(3)),
        'css': fields.String(required=True),
        'yaml': YAML(ReceiptTplMetadataSchema, required=True),
    })
    def _process(self, html, css, yaml):
        g.template_stack = [TemplateStackEntry(None)]
        # Just some dummy data to test the template
        dummy_data = _generate_dummy_data(yaml.get('custom_fields', []))
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
            yaml=self.template.yaml,
            default_filename=self.template.default_filename,
            **self.target_dict
        )
        db.session.add(new_tpl)
        db.session.flush()
        new_tpl.log(new_tpl.log_realm, LogKind.positive, 'Templates', f'Document template "{new_tpl.title}" created',
                    user=session.user, data={'Cloned from': self.template.title})
        return jsonify(ReceiptTemplateDBSchema().dump(new_tpl))
