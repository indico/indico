# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import ValidationError, fields

from indico.core import signals
from indico.core.db import db
from indico.core.marshmallow import mm
from indico.modules.events.registration.custom import RegistrationListColumn
from indico.modules.events.registration.fields.base import FieldSetupSchemaBase, RegistrationFormFieldBase
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.modules.users.models.affiliations import Affiliation
from indico.util.caching import memoize_request
from indico.util.enum import IndicoIntEnum
from indico.util.marshmallow import not_empty
from indico.util.signals import values_from_signal
from indico.web.flask.templating import get_template_module


class AffiliationMode(IndicoIntEnum):
    both = 1
    predefined = 2
    custom = 3


class AffiliationFieldDataSchema(FieldSetupSchemaBase):
    affiliation_mode = fields.Enum(AffiliationMode, by_value=True, load_default=AffiliationMode.both)


class AffiliationValueSchema(mm.Schema):
    id = fields.Integer(required=True, allow_none=True)
    text = fields.String(required=True)


@memoize_request
def _get_affiliation_details(affiliation_id):
    from indico.modules.users.schemas import AffiliationSchema
    affiliation = Affiliation.query.filter_by(id=affiliation_id, is_deleted=False).one_or_none()
    return AffiliationSchema().dump(affiliation) if affiliation else None


class AffiliationField(RegistrationFormFieldBase):
    name = 'affiliation'
    setup_schema_base_cls = AffiliationFieldDataSchema
    mm_field_class = fields.Nested
    mm_field_args = (AffiliationValueSchema,)
    not_empty_if_required = False

    def get_validators(self, existing_registration):
        def _validate_affiliation(value):
            affiliation_mode = AffiliationMode(self.form_item.data['affiliation_mode'])
            if self.form_item.is_required:
                not_empty(value['text'])
            if value['id'] is None:
                if (affiliation_mode == AffiliationMode.predefined and
                        (value['text'] or self.form_item.is_required)):
                    raise ValidationError('Please select an affiliation from the list')
                return
            if affiliation_mode == AffiliationMode.custom:
                raise ValidationError('Please enter a custom affiliation')

        return _validate_affiliation

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False):
        if isinstance(value, str):
            value = {'id': None, 'text': value}
        if value['id'] is None:
            return super().process_form_data(registration, value if value['text'] else '', old_data,
                                             billable_items_locked)

        context = {
            'event': self.form_item.registration_form.event,
            'registration_form': self.form_item.registration_form,
            'registration': registration,
            'field': self
        }
        filters = values_from_signal(signals.affiliations.get_affiliation_filters.send(self, context=context),
                                        as_list=True, multi_value_types=list)
        query = Affiliation.query.filter_by(id=value['id'], is_deleted=False)
        if filters:
            query = query.filter(*filters)
        affiliation = query.one_or_none()
        if not affiliation:
            raise ValidationError('Invalid affiliation')
        value['text'] = affiliation.name
        return super().process_form_data(registration, value, old_data, billable_items_locked)

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        data = registration_data.data
        if isinstance(data, dict):
            return data.get('text') or ''
        return data or ''

    def _render_affiliation(self, value):
        details = _get_affiliation_details(value['id']) if value['id'] is not None else None
        return get_template_module('events/_affiliation.html').render_affiliation(value['text'], details)

    def render_summary_data(self, data: RegistrationData):
        return self._render_affiliation(data.data)

    def render_reglist_column(self, data: RegistrationData) -> RegistrationListColumn:
        return RegistrationListColumn(self._render_affiliation(data.data), data.search_data)

    def create_sql_filter(self, data_list):
        return db.func.coalesce(RegistrationData.data['text'].astext, RegistrationData.data.astext).in_(data_list)

    @property
    def default_value(self):
        return {'id': None, 'text': ''}
