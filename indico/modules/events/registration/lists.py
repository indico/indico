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

from collections import OrderedDict

from flask import request
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.events.registration.models.form_fields import (RegistrationFormFieldData,
                                                                   RegistrationFormPersonalDataField)
from indico.modules.events.registration.models.items import PersonalDataType, RegistrationFormItem
from indico.modules.events.registration.models.registrations import Registration, RegistrationData, RegistrationState
from indico.modules.events.util import ListGeneratorBase
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module


class RegistrationListGenerator(ListGeneratorBase):
    """Listing and filtering actions in the registration list."""

    endpoint = '.manage_reglist'
    list_link_type = 'registration'

    def __init__(self, regform):
        super(RegistrationListGenerator, self).__init__(regform.event, entry_parent=regform)
        self.regform = regform
        self.default_list_config = {
            'items': ('title', 'email', 'affiliation', 'reg_date', 'state'),
            'filters': {'fields': {}, 'items': {}}
        }
        self.static_items = OrderedDict([
            ('reg_date', {
                'title': _('Registration Date'),
            }),
            ('price', {
                'title': _('Price'),
            }),
            ('state', {
                'title': _('State'),
                'filter_choices': {str(state.value): state.title for state in RegistrationState}
            }),
            ('checked_in', {
                'title': _('Checked in'),
                'filter_choices': {
                    '0': _('No'),
                    '1': _('Yes')
                }
            }),
            ('checked_in_date', {
                'title': _('Check-in date'),
            }),
            ('payment_date', {
                'title': _('Payment date'),
            })
        ])
        self.personal_items = ('title', 'first_name', 'last_name', 'email', 'position', 'affiliation', 'address',
                               'phone', 'country')
        self.list_config = self._get_config()

    def _get_static_columns(self, ids):
        """
        Retrieve information needed for the header of the static
        columns (including static and personal items).

        :return: a list of {'id': ..., 'caption': ...} dicts
        """
        result = []
        for item_id in ids:
            if item_id in self.personal_items:
                field = RegistrationFormItem.find_one(registration_form=self.regform,
                                                      personal_data_type=PersonalDataType[item_id])
                result.append({
                    'id': field.id,
                    'caption': field.title
                })
            elif item_id in self.static_items:
                result.append({
                    'id': item_id,
                    'caption': self.static_items[item_id]['title']
                })
        return result

    def _column_ids_to_db(self, ids):
        """Translate string-based ids to DB-based RegistrationFormItem ids."""
        result = []
        personal_data_field_ids = {x.personal_data_type: x.id for x in self.regform.form_items if x.is_field}
        for item_id in ids:
            if isinstance(item_id, basestring):
                personal_data_type = PersonalDataType.get(item_id)
                if personal_data_type:
                    item_id = personal_data_field_ids[personal_data_type]
            result.append(item_id)
        return result

    def _get_sorted_regform_items(self, item_ids):
        """Return the form items ordered by their position in the registration form."""

        if not item_ids:
            return []
        return (RegistrationFormItem
                .find(~RegistrationFormItem.is_deleted, RegistrationFormItem.id.in_(item_ids))
                .with_parent(self.regform)
                .join(RegistrationFormItem.parent, aliased=True)
                .filter(~RegistrationFormItem.is_deleted)  # parent deleted
                .order_by(RegistrationFormItem.position)  # parent position
                .reset_joinpoint()
                .order_by(RegistrationFormItem.position)  # item position
                .all())

    def _get_filters_from_request(self):
        filters = super(RegistrationListGenerator, self)._get_filters_from_request()
        for field in self.regform.form_items:
            if field.is_field and field.input_type in {'single_choice', 'multi_choice', 'country', 'bool', 'checkbox'}:
                options = request.form.getlist('field_{}'.format(field.id))
                if options:
                    filters['fields'][str(field.id)] = options
        return filters

    def _build_query(self):
        return (Registration.query
                .with_parent(self.regform)
                .filter(~Registration.is_deleted)
                .options(joinedload('data').joinedload('field_data').joinedload('field'))
                .order_by(db.func.lower(Registration.last_name), db.func.lower(Registration.first_name)))

    def _filter_list_entries(self, query, filters):
        if not (filters.get('fields') or filters.get('items')):
            return query
        field_types = {str(f.id): f.field_impl for f in self.regform.form_items
                       if f.is_field and not f.is_deleted and (f.parent_id is None or not f.parent.is_deleted)}
        field_filters = {field_id: data_list
                         for field_id, data_list in filters['fields'].iteritems()
                         if field_id in field_types}
        if not field_filters and not filters['items']:
            return query
        criteria = [db.and_(RegistrationFormFieldData.field_id == field_id,
                            field_types[field_id].create_sql_filter(data_list))
                    for field_id, data_list in field_filters.iteritems()]
        items_criteria = []
        if 'checked_in' in filters['items']:
            checked_in_values = filters['items']['checked_in']
            # If both values 'true' and 'false' are selected, there's no point in filtering
            if len(checked_in_values) == 1:
                items_criteria.append(Registration.checked_in == bool(int(checked_in_values[0])))

        if 'state' in filters['items']:
            states = [RegistrationState(int(state)) for state in filters['items']['state']]
            items_criteria.append(Registration.state.in_(states))

        if field_filters:
            subquery = (RegistrationData.query
                        .with_entities(db.func.count(RegistrationData.registration_id))
                        .join(RegistrationData.field_data)
                        .filter(RegistrationData.registration_id == Registration.id)
                        .filter(db.or_(*criteria))
                        .correlate(Registration)
                        .as_scalar())
            query = query.filter(subquery == len(field_filters))
        return query.filter(db.or_(*items_criteria))

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
