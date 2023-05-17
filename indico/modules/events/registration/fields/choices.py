# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import sys
from collections import Counter
from copy import deepcopy
from datetime import date, datetime
from uuid import uuid4

from marshmallow import ValidationError, fields, post_load, pre_load, validate, validates_schema
from sqlalchemy.dialects.postgresql import ARRAY

from indico.core.db import db
from indico.core.marshmallow import mm
from indico.modules.events.registration.fields.base import (LimitedPlacesBillableFieldDataSchema,
                                                            RegistrationFormBillableField,
                                                            RegistrationFormBillableItemsField)
from indico.modules.events.registration.models.form_fields import RegistrationFormFieldData
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.util.date_time import format_date
from indico.util.i18n import _
from indico.util.marshmallow import UUIDString, not_empty
from indico.util.string import camelize_keys, snakify_keys


def get_field_merged_options(field, registration_data):
    rdata = registration_data.get(field.id)
    result = deepcopy(field.view_data)
    if not rdata or not rdata.data:
        return result
    values = [rdata.data['choice']] if 'choice' in rdata.data else [k for k, v in rdata.data.items() if v]
    for val in values:
        if val and not any(item['id'] == val for item in result['choices']):
            field_data = rdata.field_data
            merged_data = field.field_impl.unprocess_field_data(field_data.versioned_data,
                                                                field_data.field.data)
            missing_option = next((choice for choice in merged_data['choices'] if choice['id'] == val), None)
            if missing_option:
                result['choices'].append(camelize_keys(missing_option) | {'_deleted': True})
        else:
            current_choice_data = _get_choice_by_id(val, result['choices'])
            registration_choice_data = dict(camelize_keys(
                _get_choice_by_id(val, rdata.field_data.versioned_data.get('choices', {}))),
                caption=current_choice_data['caption'])
            if current_choice_data != registration_choice_data:
                pos = result['choices'].index(current_choice_data)
                result['choices'][pos] = registration_choice_data | {'_modified': True}
    return result


def _get_choice_by_id(choice_id, choices):
    for choice in choices:
        if choice['id'] == choice_id:
            return choice


class ChoiceItemSchema(LimitedPlacesBillableFieldDataSchema):
    id = fields.UUID()
    is_enabled = fields.Bool(required=True)
    max_extra_slots = fields.Integer(load_default=0, validate=validate.Range(0, 99))
    extra_slots_pay = fields.Bool(load_default=False)
    caption = fields.String(required=True, validate=not_empty)

    @post_load
    def _stringify_uuid(self, data, **kwargs):
        if 'id' in data:
            data['id'] = str(data['id'])
        return data


class ChoiceSetupSchema(mm.Schema):
    with_extra_slots = fields.Bool(load_default=False)
    choices = fields.List(fields.Nested(ChoiceItemSchema), required=True, validate=not_empty)

    @pre_load
    def _generate_new_uuids(self, data, **kwrags):
        data = data.copy()
        if 'choices' in data:
            # generate uuids for the random client-side IDs
            data['choices'] = data['choices'].copy()
            for c in data['choices']:
                orig_id = c.get('id', '')
                if orig_id.startswith('new:'):
                    c['id'] = str(uuid4())
                    if data.get('default_item') == orig_id:
                        data['default_item'] = c['id']
        return data


class SingleChoiceSetupSchema(ChoiceSetupSchema):
    default_item = fields.String(load_default=None)
    item_type = fields.String(required=True, validate=validate.OneOf(['dropdown', 'radiogroup']))

    @validates_schema(skip_on_field_errors=True)
    def _validate_default_item(self, data, **kwargs):
        ids = {c['id'] for c in data['choices']}
        if data['default_item'] and data['default_item'] not in ids:
            raise ValidationError('Invalid default item', 'default_item')


class ChoiceBaseField(RegistrationFormBillableItemsField):
    versioned_data_fields = RegistrationFormBillableItemsField.versioned_data_fields | {'choices'}
    has_default_item = False
    mm_field_class = fields.Dict
    mm_field_kwargs = {'keys': fields.String(), 'values': fields.Integer()}

    @classmethod
    def unprocess_field_data(cls, versioned_data, unversioned_data):
        items = deepcopy(versioned_data['choices'])
        for item in items:
            item['caption'] = unversioned_data['captions'][item['id']]
        return {'choices': items}

    @property
    def filter_choices(self):
        return self.form_item.data['captions']

    @property
    def view_data(self):
        return dict(super().view_data, places_used=self.get_places_used())

    def get_validators(self, existing_registration):
        def _check_number_of_places(new_data):
            if not new_data:
                return True
            old_data = None
            if existing_registration:
                old_data = existing_registration.data_by_field.get(self.form_item.id)
                if old_data and not self.has_data_changed(new_data, old_data):
                    return
            choices = self.form_item.versioned_data['choices']
            captions = self.form_item.data['captions']
            for k in new_data:
                choice = next((x for x in choices if x['id'] == k), None)
                # Need to check the selected choice, because it might have been deleted.
                if choice:
                    places_limit = choice.get('places_limit')
                    places_used_dict = self.get_places_used()
                    places_used_dict.setdefault(k, 0)
                    if old_data and old_data.data:
                        places_used_dict[k] -= old_data.data.get(k, 0)
                    places_used_dict[k] += new_data[k]
                    if places_limit and (places_limit - places_used_dict.get(k, 0)) < 0:
                        raise ValidationError(_('No places left for the option: {0}').format(captions[k]))
        return [_check_number_of_places]

    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        unversioned_data, versioned_data = super().process_field_data(data, old_data, old_versioned_data)
        items = [x for x in versioned_data['choices'] if not x.get('remove')]
        captions = dict(old_data['captions']) if old_data is not None else {}
        if cls.has_default_item:
            unversioned_data.setdefault('default_item', None)
        for item in items:
            if 'id' not in item:
                item['id'] = str(uuid4())
            assert 'is_billable' not in item
            item['price'] = float(item['price']) if item.get('price') else 0
            item['places_limit'] = int(item['places_limit']) if item.get('places_limit') else 0
            item['max_extra_slots'] = int(item['max_extra_slots']) if item.get('max_extra_slots') else 0
            if cls.has_default_item and unversioned_data['default_item'] == item['id']:
                unversioned_data['default_item'] = item['id']
            captions[item['id']] = item.pop('caption')
        versioned_data['choices'] = items
        unversioned_data['captions'] = captions
        return unversioned_data, versioned_data

    def get_places_used(self):
        places_used = Counter()
        if not any(x.get('places_limit') for x in self.form_item.versioned_data['choices']):
            return dict(places_used)
        for registration in self.form_item.registration_form.active_registrations:
            if self.form_item.id not in registration.data_by_field:
                continue
            data = registration.data_by_field[self.form_item.id].data
            if not data:
                continue
            places_used.update(data)
        return dict(places_used)

    def create_sql_filter(self, data_list):
        return RegistrationData.data.has_any(db.func.cast(data_list, ARRAY(db.String)))

    def calculate_price(self, reg_data, versioned_data):
        if not reg_data:
            return 0
        billable_choices = [x for x in versioned_data['choices'] if x['id'] in reg_data and x['price']]
        price = 0
        for billable_field in billable_choices:
            price += billable_field['price']
            if billable_field.get('extra_slots_pay'):
                price += (reg_data[billable_field['id']] - 1) * billable_field['price']
        return price


class SingleChoiceField(ChoiceBaseField):
    name = 'single_choice'
    has_default_item = True
    setup_schema_base_cls = SingleChoiceSetupSchema

    @property
    def default_value(self):
        data = self.form_item.data
        versioned_data = self.form_item.versioned_data
        try:
            default_item = data['default_item']
        except KeyError:
            return None
        # only use the default item if it exists in the current version
        return {default_item: 1} if any(x['id'] == default_item for x in versioned_data['choices']) else {}

    @property
    def empty_value(self):
        return {}

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        if not registration_data.data:
            return ''
        uuid, number_of_slots = list(registration_data.data.items())[0]
        caption = registration_data.field_data.field.data['captions'][uuid]
        return f'{caption} (+{number_of_slots - 1})' if number_of_slots > 1 else caption

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False, new_data_version=None):
        if billable_items_locked and old_data.price:
            # if the old field was paid we can simply ignore any change and keep the old value
            return {}
        # always store no-option as empty dict
        if value is None:
            value = {}
        # get rid of entries with 0 slots; they shouldn't happen at all but just in case
        value = {k: v for k, v in value.items() if v}
        return super().process_form_data(registration, value, old_data, billable_items_locked, new_data_version)


def _hashable_choice(choice):
    return frozenset(choice.items())


class MultiChoiceField(ChoiceBaseField):
    name = 'multi_choice'
    setup_schema_base_cls = ChoiceSetupSchema

    @property
    def default_value(self):
        return {}

    def _get_display_index(self, choice_order, uuid):
        try:
            return choice_order.index(uuid)
        except ValueError:
            return sys.maxsize

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        def _format_item(uuid, number_of_slots):
            caption = self.form_item.data['captions'][uuid]
            return f'{caption} (+{number_of_slots - 1})' if number_of_slots > 1 else caption

        reg_data = registration_data.data

        if not reg_data:
            return ''

        # Preserve the original multi choice field order given by
        # the field when getting the selected choices.
        field_choice_order = [x['id'] for x in registration_data.field_data.field.view_data['choices']]
        reg_data = dict(sorted(reg_data.items(), key=lambda x: self._get_display_index(field_choice_order, x[0])))
        choices = [_format_item(uuid, number_of_slots) for uuid, number_of_slots in reg_data.items()]

        return ', '.join(choices) if for_humans or for_search else choices

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False, new_data_version=None):
        # always store no-option as empty dict
        if value is None:
            value = {}
        # get rid of entries with 0 slots; they're filtered client-side but just in case...
        value = {k: v for k, v in value.items() if v}

        return_value = {}
        has_old_data = old_data is not None and old_data.data is not None

        if has_old_data:
            # in case nothing changed we can skip all checks
            if old_data.data == value:
                return {}

            selected_choice_hashes = {c['id']: _hashable_choice(c)
                                      for c in old_data.field_data.versioned_data['choices']
                                      if c['id'] in value}
            selected_choice_hashes.update({c['id']: _hashable_choice(c)
                                           for c in self.form_item.versioned_data['choices']
                                           if c['id'] in value and c['id'] not in selected_choice_hashes})
            selected_choice_hashes = set(selected_choice_hashes.values())
            existing_version_hashes = {c['id']: _hashable_choice(c)
                                       for c in old_data.field_data.versioned_data['choices']}
            latest_version_hashes = {c['id']: _hashable_choice(c) for c in self.form_item.versioned_data['choices']}
            deselected_ids = old_data.data.keys() - value.keys()
            modified_deselected = any(latest_version_hashes.get(id_) != existing_version_hashes.get(id_)
                                      for id_ in deselected_ids)
            if selected_choice_hashes <= set(latest_version_hashes.values()):
                # all choices available in the latest version - upgrade to that version
                return_value['field_data'] = self.form_item.current_data
            elif not modified_deselected and selected_choice_hashes <= set(existing_version_hashes.values()):
                # all choices available in the previously selected version - stay with it
                return_value['field_data'] = old_data.field_data
            else:
                # create a new version containing selected choices from the previously
                # selected version and everything else from the latest version
                new_choices = []
                used_ids = set()
                for choice in old_data.field_data.versioned_data['choices']:
                    # copy all old choices that are currently selected
                    if choice['id'] in value:
                        used_ids.add(choice['id'])
                        new_choices.append(choice)
                for choice in self.form_item.versioned_data['choices']:
                    # copy all new choices unless we already got them from the old version
                    if choice['id'] not in used_ids:
                        used_ids.add(choice['id'])
                        new_choices.append(choice)
                new_choices_hash = {_hashable_choice(x) for x in new_choices}
                for data_version in self.form_item.data_versions:
                    if {_hashable_choice(x) for x in data_version.versioned_data['choices']} == new_choices_hash:
                        break
                else:
                    data_version = RegistrationFormFieldData(field=self.form_item,
                                                             versioned_data={'choices': new_choices})
                return_value['field_data'] = data_version
            new_choices = return_value['field_data'].versioned_data['choices']

        if not billable_items_locked:
            processed_data = super().process_form_data(registration, value, old_data, False,
                                                       return_value.get('field_data'))
            return {key: return_value.get(key, value) for key, value in processed_data.items()}
        # XXX: This code still relies on the client sending data for the disabled fields.
        # This is pretty ugly but especially in case of non-billable extra slots it makes
        # sense to keep it like this.  If someone tampers with the list of billable fields
        # we detect it any reject the change to the field's data anyway.
        if has_old_data:
            old_choices_mapping = {x['id']: x for x in old_data.field_data.versioned_data['choices']}
            new_choices_mapping = {x['id']: x for x in new_choices}
            old_billable = {uuid: num for uuid, num in old_data.data.items() if old_choices_mapping[uuid]['price']}
            new_billable = {uuid: num for uuid, num in value.items() if new_choices_mapping[uuid]['price']}
        if has_old_data and old_billable != new_billable:
            # preserve existing data
            return return_value
        else:
            # nothing price-related changed
            # TODO: check item prices (in case there's a change between old/new version)
            # for now we simply ignore field changes in this case (since the old/new price
            # check in the base method will fail)
            processed_data = super().process_form_data(registration, value, old_data, True,
                                                       return_value.get('field_data'))
            return {key: return_value.get(key, value) for key, value in processed_data.items()}


def _to_machine_date(date):
    return date.strftime('%Y-%m-%d')


def _to_date(date):
    return datetime.strptime(date, '%Y-%m-%d').date()


class AccommodationItemSchema(LimitedPlacesBillableFieldDataSchema):
    id = fields.UUID()
    is_enabled = fields.Bool(required=True)
    is_no_accommodation = fields.Bool(load_default=False)
    caption = fields.String(required=True, validate=not_empty)

    @pre_load
    def _remove_garbage(self, data, **kwargs):
        # legacy leftover
        data.pop('placeholder', None)
        return data

    @post_load
    def _stringify_uuid(self, data, **kwargs):
        if 'id' in data:
            data['id'] = str(data['id'])
        return data


class AccommodationDateRangeSchema(mm.Schema):
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    @validates_schema(skip_on_field_errors=True)
    def _validate_dates(self, data, **kwargs):
        if data['start_date'] > data['end_date']:
            raise ValidationError('The end date cannot be before the start date', 'end_date')


class AccommodationSetupSchema(mm.Schema):
    choices = fields.List(fields.Nested(AccommodationItemSchema), required=True, validate=not_empty)
    arrival = fields.Nested(AccommodationDateRangeSchema, required=True)
    departure = fields.Nested(AccommodationDateRangeSchema, required=True)

    @validates_schema(skip_on_field_errors=True)
    def _validate_periods(self, data, **kwargs):
        if data['departure']['start_date'] < data['arrival']['start_date']:
            raise ValidationError('The departure period cannot begin before the arrival period.', 'departure')
        if data['arrival']['end_date'] > data['departure']['end_date']:
            raise ValidationError('The arrival period cannot end after the departure period.', 'arrival')

    @pre_load
    def _generate_new_uuids(self, data, **kwrags):
        data = data.copy()
        if 'choices' in data:
            # generate uuids for the random client-side IDs
            data['choices'] = data['choices'].copy()
            for c in data['choices']:
                if c.get('id', '').startswith('new:'):
                    c['id'] = str(uuid4())
        return data

    @post_load
    def _split_dates(self, data, **kwargs):
        data['arrival_date_from'] = data['arrival']['start_date']
        data['arrival_date_to'] = data['arrival']['end_date']
        data['departure_date_from'] = data['departure']['start_date']
        data['departure_date_to'] = data['departure']['end_date']
        del data['arrival']
        del data['departure']
        return data


class AccommodationSchema(mm.Schema):
    choice = UUIDString()
    isNoAccommodation = fields.Bool(load_default=False)  # noqa: N815
    arrivalDate = fields.Date(allow_none=True)  # noqa: N815
    departureDate = fields.Date(allow_none=True)  # noqa: N815

    @validates_schema(skip_on_field_errors=True)
    def validate_everything(self, data, **kwargs):
        if not data['isNoAccommodation']:
            if not data['choice']:
                raise ValidationError('Choice is required', 'choice')
            elif not data.get('arrivalDate'):
                raise ValidationError('Arrival date is required', 'arrivalDate')
            elif not data.get('departureDate'):
                raise ValidationError('Departure date is required', 'departureDate')


class AccommodationField(RegistrationFormBillableItemsField):
    name = 'accommodation'
    versioned_data_fields = RegistrationFormBillableField.versioned_data_fields | {'choices'}
    setup_schema_base_cls = AccommodationSetupSchema
    mm_field_class = fields.Nested
    mm_field_args = (AccommodationSchema,)

    @property
    def default_value(self):
        versioned_data = self.form_item.versioned_data
        no_accommodation_option = next(
            (c for c in versioned_data['choices'] if c.get('is_no_accommodation') and c['is_enabled']), None)
        return {
            'choice': no_accommodation_option['id'] if no_accommodation_option else None,
            'isNoAccommodation': bool(no_accommodation_option),
            'arrivalDate': None,
            'departureDate': None,
        }

    @property
    def empty_value(self):
        return {'choice': None}

    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        unversioned_data, versioned_data = super().process_field_data(data, old_data, old_versioned_data)
        items = [x for x in versioned_data['choices'] if not x.get('remove')]
        captions = dict(old_data['captions']) if old_data is not None else {}
        for item in items:
            if 'id' not in item:
                item['id'] = str(uuid4())
            assert 'is_billable' not in item
            item['price'] = float(item['price']) if item.get('price') else 0
            item['places_limit'] = int(item['places_limit']) if item.get('places_limit') else 0
            captions[item['id']] = item.pop('caption')
        for key in {'arrival_date_from', 'arrival_date_to', 'departure_date_from', 'departure_date_to'}:
            unversioned_data[key] = _to_machine_date(unversioned_data[key])
        versioned_data['choices'] = items
        unversioned_data['captions'] = captions
        return unversioned_data, versioned_data

    @classmethod
    def unprocess_field_data(cls, versioned_data, unversioned_data):
        data = {}
        data['arrival'] = {
            'start_date': unversioned_data['arrival_date_from'],
            'end_date': unversioned_data['arrival_date_to'],
        }
        data['departure'] = {
            'start_date': unversioned_data['departure_date_from'],
            'end_date': unversioned_data['departure_date_to'],
        }
        items = deepcopy(versioned_data['choices'])
        for item in items:
            item['caption'] = unversioned_data['captions'][item['id']]
        data['choices'] = items
        return data

    def get_validators(self, existing_registration):
        def _check_choice_data(new_data):
            item = None
            if existing_registration:
                old_data = existing_registration.data_by_field.get(self.form_item.id)
                if old_data and not self.has_data_changed(snakify_keys(new_data), old_data):
                    return
                elif old_data:
                    # try to get choice from existing data
                    item = next((c for c in old_data.field_data.versioned_data['choices']
                                 if c['id'] == new_data['choice']), None)
            if item is None:
                item = next((c for c in self.form_item.versioned_data['choices'] if c['id'] == new_data['choice']),
                            None)
            # this should never happen unless someone tampers with the data
            if item is None or not item['is_enabled']:
                raise ValidationError('Invalid choice')
            if item.get('is_no_accommodation', False) != new_data['isNoAccommodation']:
                raise ValidationError('Invalid data')

        def _stay_dates_valid(new_data):
            if not new_data:
                return True
            data = snakify_keys(new_data)
            if not data.get('is_no_accommodation'):
                try:
                    arrival_date = data['arrival_date']
                    departure_date = data['departure_date']
                except KeyError:
                    raise ValidationError(_('Arrival/departure date is missing'))
                if arrival_date > departure_date:
                    raise ValidationError(_("Arrival date can't be set after the departure date."))

        def _check_number_of_places(new_data):
            if not new_data:
                return True
            if existing_registration:
                old_data = existing_registration.data_by_field.get(self.form_item.id)
                if old_data and not self.has_data_changed(snakify_keys(new_data), old_data):
                    return
            item = next((x for x in self.form_item.versioned_data['choices'] if x['id'] == new_data['choice']),
                        None)
            captions = self.form_item.data['captions']
            places_used_dict = self.get_places_used()
            if (item and item['places_limit'] and
                    (item['places_limit'] < places_used_dict.get(new_data['choice'], 0))):
                raise ValidationError(_("Not enough rooms in '{0}'").format(captions[item['id']]))

        return [_check_choice_data, _stay_dates_valid, _check_number_of_places]

    @property
    def view_data(self):
        return dict(super().view_data, places_used=self.get_places_used())

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        if not registration_data.data:
            return '' if for_humans or for_search else {}
        friendly_data = dict(registration_data.data)
        unversioned_data = registration_data.field_data.field.data
        friendly_data['choice'] = unversioned_data['captions'][friendly_data['choice']]
        if not friendly_data.get('is_no_accommodation'):
            friendly_data['arrival_date'] = _to_date(friendly_data['arrival_date'])
            friendly_data['departure_date'] = _to_date(friendly_data['departure_date'])
            friendly_data['nights'] = (friendly_data['departure_date'] - friendly_data['arrival_date']).days
        else:
            friendly_data['arrival_date'] = ''
            friendly_data['departure_date'] = ''
            friendly_data['nights'] = 0
        return friendly_data['choice'] if for_humans or for_search else friendly_data

    def calculate_price(self, reg_data, versioned_data):
        if not reg_data:
            return 0
        item = next((x for x in versioned_data['choices'] if reg_data['choice'] == x['id'] and x['price']), None)
        if not item:
            return 0
        nights = (_to_date(reg_data['departure_date']) - _to_date(reg_data['arrival_date'])).days
        return item['price'] * nights

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False, new_data_version=None):
        if billable_items_locked and old_data.price:
            # if the old field was paid we can simply ignore any change and keep the old data
            return {}
        data = {}
        if value:
            is_no_accommodation = value.get('isNoAccommodation', False)
            data = {'choice': value['choice'],
                    'is_no_accommodation': is_no_accommodation}
            if not is_no_accommodation:
                data.update({'arrival_date': value['arrivalDate'].isoformat(),
                             'departure_date': value['departureDate'].isoformat()})
        return super().process_form_data(registration, data, old_data, billable_items_locked, new_data_version)

    def get_places_used(self):
        places_used = Counter()
        if not any(x.get('places_limit') for x in self.form_item.versioned_data['choices']):
            return dict(places_used)
        for registration in self.form_item.registration_form.active_registrations:
            if self.form_item.id not in registration.data_by_field:
                continue
            data = registration.data_by_field[self.form_item.id].data
            if not data:
                continue
            places_used.update((data['choice'],))
        return dict(places_used)

    def iter_placeholder_info(self):
        yield 'name', f'Accommodation name for "{self.form_item.title}" ({self.form_item.parent.title})'
        yield 'nights', f'Number of nights for "{self.form_item.title}" ({self.form_item.parent.title})'
        yield 'arrival', f'Arrival date for "{self.form_item.title}" ({self.form_item.parent.title})'
        yield 'departure', f'Departure date for "{self.form_item.title}" ({self.form_item.parent.title})'

    def render_placeholder(self, data, key=None):
        mapping = {'name': 'choice',
                   'nights': 'nights',
                   'arrival': 'arrival_date',
                   'departure': 'departure_date'}
        rv = self.get_friendly_data(data).get(mapping[key], '')
        return format_date(rv) if isinstance(rv, date) else rv
