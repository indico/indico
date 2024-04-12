# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request
from sqlalchemy.orm import joinedload, undefer

from indico.core.db import db
from indico.modules.events.registration.models.form_fields import RegistrationFormFieldData
from indico.modules.events.registration.models.items import PersonalDataType, RegistrationFormItem
from indico.modules.events.registration.models.registrations import (Registration, RegistrationData, RegistrationState,
                                                                     RegistrationVisibility)
from indico.modules.events.registration.models.tags import RegistrationTag
from indico.modules.events.util import ListGeneratorBase
from indico.util.i18n import _
from indico.util.string import natural_sort_key
from indico.web.flask.templating import get_template_module


class RegistrationListGenerator(ListGeneratorBase):
    """Listing and filtering actions in the registration list."""

    endpoint = '.manage_reglist'
    list_link_type = 'registration'

    def __init__(self, regform):
        super().__init__(regform.event, entry_parent=regform)
        self.regform = regform
        self.default_list_config = {
            'items': ('title', 'email', 'affiliation', 'reg_date', 'state', 'tags_present'),
            'filters': {'fields': {}, 'items': {}}
        }
        registration_tag_choices = self._get_registration_tag_choices()
        self.static_items = {
            'reg_date': {
                'title': _('Registration Date'),
            },
            'price': {
                'title': _('Price'),
            },
            'state': {
                'title': _('State'),
                'filter_choices': {str(state.value): state.title for state in RegistrationState}
            },
            'checked_in': {
                'title': _('Checked in'),
                'filter_choices': {
                    '0': _('No'),
                    '1': _('Yes')
                }
            },
            'checked_in_date': {
                'title': _('Check-in date'),
            },
            'payment_date': {
                'title': _('Payment date'),
            },
            'visibility': {
                'title': _('Visibility'),
            },
            'consent_to_publish': {
                'title': _('Consent to publish'),
                'filter_choices': {str(visibility.value): visibility.title for visibility in RegistrationVisibility}
            },
            'participant_hidden': {
                'title': _('Participant hidden'),
                'filter_choices': {
                    '0': _('No'),
                    '1': _('Yes')
                }
            },
            'tags_present': {
                'title': _('Tags'),
                'filter_title': _('Has tags'),
                'filter_choices': registration_tag_choices
            },
            'tags_absent': {
                'title': _('Tags absent'),
                'filter_title': _('Does not have tags'),
                'filter_choices': registration_tag_choices,
                'filter_only': True
            },
            'receipts_present': {
                'title': _('Has documents'),
                'filter_choices': {
                    '0': _('No'),
                    '1': _('Yes')
                }
            },
        }
        self.personal_items = ('title', 'first_name', 'last_name', 'email', 'position', 'affiliation', 'address',
                               'phone', 'country', 'picture')
        self.list_config = self._get_config()

    def _get_registration_tag_choices(self):
        tags = sorted(self.event.registration_tags, key=lambda tag: natural_sort_key(tag.title))
        return {str(tag.id): tag.title for tag in tags}

    def _get_static_columns(self, ids):
        """
        Retrieve information needed for the header of the static
        columns (including static and personal items).

        :return: a list of {'id': ..., 'caption': ...} dicts
        """
        ids = set(ids)
        result = []
        for item_id in [x for x in self.personal_items if x in ids]:
            field = RegistrationFormItem.query.filter_by(registration_form=self.regform,
                                                         personal_data_type=PersonalDataType[item_id]).one()
            result.append({'id': field.id, 'caption': field.title})
        for item_id in [x for x in self.static_items if x in ids]:
            result.append({'id': item_id, 'caption': self.static_items[item_id]['title']})  # noqa: PERF401
        return result

    def _column_ids_to_db(self, ids):
        """Translate string-based ids to DB-based RegistrationFormItem ids."""
        result = []
        personal_data_field_ids = {x.personal_data_type: x.id for x in self.regform.form_items if x.is_field}
        for item_id in ids:
            if isinstance(item_id, str):
                personal_data_type = PersonalDataType.get(item_id)
                if personal_data_type:
                    item_id = personal_data_field_ids[personal_data_type]
            result.append(item_id)
        return result

    def _get_sorted_regform_items(self, item_ids):
        """Return the form items ordered by their position in the registration form."""
        if not item_ids:
            return []
        return (RegistrationFormItem.query
                .filter(~RegistrationFormItem.is_deleted, RegistrationFormItem.id.in_(item_ids))
                .with_parent(self.regform)
                .join(RegistrationFormItem.parent, aliased=True)
                .filter(~RegistrationFormItem.is_deleted)  # parent deleted
                .order_by(RegistrationFormItem.position)  # parent position
                .reset_joinpoint()
                .order_by(RegistrationFormItem.position)  # item position
                .all())

    def _get_filters_from_request(self):
        filters = super()._get_filters_from_request()
        for field in self.regform.form_items:
            if field.is_field and field.input_type in {'single_choice', 'multi_choice', 'country', 'bool', 'checkbox',
                                                       'sessions'}:
                options = request.form.getlist(f'field_{field.id}')
                if options:
                    filters['fields'][str(field.id)] = options
        return filters

    def _build_query(self):
        return (Registration.query
                .with_parent(self.regform)
                .filter(~Registration.is_deleted)
                .options(joinedload('data').joinedload('field_data').joinedload('field'),
                         joinedload('tags'),
                         undefer('num_receipt_files'))
                .order_by(db.func.lower(Registration.last_name), db.func.lower(Registration.first_name)))

    def _filter_list_entries(self, query, filters):
        if not (filters.get('fields') or filters.get('items')):
            return query
        field_types = {str(f.id): f.field_impl for f in self.regform.form_items
                       if f.is_field and not f.is_deleted and (f.parent_id is None or not f.parent.is_deleted)}
        field_filters = {field_id: data_list
                         for field_id, data_list in filters['fields'].items()
                         if field_id in field_types}
        if not field_filters and not filters['items']:
            return query
        criteria = [db.and_(RegistrationFormFieldData.field_id == field_id,
                            field_types[field_id].create_sql_filter(data_list))
                    for field_id, data_list in field_filters.items()]
        items_criteria = []
        if 'checked_in' in filters['items']:
            checked_in_values = filters['items']['checked_in']
            # If both values 'true' and 'false' are selected, there's no point in filtering
            if len(checked_in_values) == 1:
                items_criteria.append(Registration.checked_in == bool(int(checked_in_values[0])))

        if 'state' in filters['items']:
            states = [RegistrationState(int(state)) for state in filters['items']['state']]
            items_criteria.append(Registration.state.in_(states))

        if 'consent_to_publish' in filters['items']:
            states = [RegistrationVisibility(int(visibility)) for visibility in filters['items']['consent_to_publish']]
            items_criteria.append(Registration.consent_to_publish.in_(states))

        if 'participant_hidden' in filters['items']:
            participant_hidden_values = filters['items']['participant_hidden']
            # If both values 'true' and 'false' are selected, there's no point in filtering
            if len(participant_hidden_values) == 1:
                items_criteria.append(Registration.participant_hidden == bool(int(participant_hidden_values[0])))

        if 'tags_present' in filters['items']:
            tag_ids = [int(tag_id) for tag_id in filters['items']['tags_present']]
            items_criteria.append(Registration.tags.any(RegistrationTag.id.in_(tag_ids)))

        if 'tags_absent' in filters['items']:
            tag_ids = [int(tag_id) for tag_id in filters['items']['tags_absent']]
            items_criteria.append(~Registration.tags.any(RegistrationTag.id.in_(tag_ids)))

        if 'receipts_present' in filters['items']:
            receipts_present_values = filters['items']['receipts_present']
            # If both values 'true' and 'false' are selected, there's no point in filtering
            if len(receipts_present_values) == 1:
                items_criteria.append(Registration.receipt_files.any() == bool(int(receipts_present_values[0])))

        if field_filters:
            subquery = (RegistrationData.query
                        .with_entities(db.func.count(RegistrationData.registration_id))
                        .join(RegistrationData.field_data)
                        .filter(RegistrationData.registration_id == Registration.id)
                        .filter(db.or_(*criteria))
                        .correlate(Registration)
                        .scalar_subquery())
            query = query.filter(subquery == len(field_filters))
        return query.filter(db.and_(*items_criteria))

    def get_list_kwargs(self):
        reg_list_config = self._get_config()
        registrations_query = self._build_query()
        total_entries = registrations_query.count()
        registrations = self._filter_list_entries(registrations_query, reg_list_config['filters']).all()
        dynamic_item_ids, static_item_ids = self._split_item_ids(reg_list_config['items'], 'dynamic')
        static_columns = self._get_static_columns(static_item_ids)
        regform_items = self._get_sorted_regform_items(dynamic_item_ids)
        return {
            'regform': self.regform,
            'registrations': registrations,
            'total_registrations': total_entries,
            'static_columns': static_columns,
            'dynamic_columns': regform_items,
            'filtering_enabled': total_entries != len(registrations)
        }

    def get_list_export_config(self):
        static_item_ids, item_ids = self.get_item_ids()
        return {
            'static_item_ids': static_item_ids,
            'regform_items': self._get_sorted_regform_items(item_ids)
        }

    def get_item_ids(self):
        reg_list_config = self._get_config()
        static_item_ids, item_ids = self._split_item_ids(reg_list_config['items'], 'static')
        return static_item_ids, self._column_ids_to_db(item_ids)

    def render_list(self):
        reg_list_kwargs = self.get_list_kwargs()
        tpl = get_template_module('events/registration/management/_reglist.html')
        filtering_enabled = reg_list_kwargs.pop('filtering_enabled')
        return {
            'html': tpl.render_registration_list(**reg_list_kwargs),
            'filtering_enabled': filtering_enabled
        }
