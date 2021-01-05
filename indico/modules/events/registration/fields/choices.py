# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import Counter
from copy import deepcopy
from datetime import date, datetime
from uuid import uuid4

from sqlalchemy.dialects.postgresql import ARRAY
from wtforms.validators import ValidationError

from indico.core.db import db
from indico.modules.events.registration.fields.base import (RegistrationFormBillableField,
                                                            RegistrationFormBillableItemsField)
from indico.modules.events.registration.models.form_fields import RegistrationFormFieldData
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.util.date_time import format_date, iterdays
from indico.util.i18n import _
from indico.util.string import camelize_keys, snakify_keys
from indico.web.forms.fields import JSONField


def get_field_merged_options(field, registration_data):
    rdata = registration_data.get(field.id)
    result = deepcopy(field.view_data)
    result['deletedChoice'] = []
    result['modifiedChoice'] = []
    if not rdata or not rdata.data:
        return result
    values = [rdata.data['choice']] if 'choice' in rdata.data else rdata.data.keys()
    for val in values:
        if val and not any(item['id'] == val for item in result['choices']):
            field_data = rdata.field_data
            merged_data = field.field_impl.unprocess_field_data(field_data.versioned_data,
                                                                field_data.field.data)
            missing_option = next((choice for choice in merged_data['choices'] if choice['id'] == val), None)
            if missing_option:
                result['choices'].append(missing_option)
                result['deletedChoice'].append(missing_option['id'])
        else:
            current_choice_data = _get_choice_by_id(val, result['choices'])
            registration_choice_data = dict(camelize_keys(
                _get_choice_by_id(val, rdata.field_data.versioned_data.get('choices', {}))),
                caption=current_choice_data['caption'])
            if current_choice_data != registration_choice_data:
                pos = result['choices'].index(current_choice_data)
                result['choices'][pos] = registration_choice_data
                result['modifiedChoice'].append(val)
    return result


def _get_choice_by_id(choice_id, choices):
    for choice in choices:
        if choice['id'] == choice_id:
            return choice


class ChoiceBaseField(RegistrationFormBillableItemsField):
    versioned_data_fields = RegistrationFormBillableItemsField.versioned_data_fields | {'choices'}
    has_default_item = False
    wtf_field_class = JSONField

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
        return dict(super(ChoiceBaseField, self).view_data, places_used=self.get_places_used())

    @property
    def validators(self):
        def _check_number_of_places(form, field):
            if not field.data:
                return
            old_data = None
            if form.modified_registration:
                old_data = form.modified_registration.data_by_field.get(self.form_item.id)
                if not old_data or not self.has_data_changed(field.data, old_data):
                    return
            choices = self.form_item.versioned_data['choices']
            captions = self.form_item.data['captions']
            for k in field.data:
                choice = next((x for x in choices if x['id'] == k), None)
                # Need to check the selected choice, because it might have been deleted.
                if choice:
                    places_limit = choice.get('places_limit')
                    places_used_dict = self.get_places_used()
                    places_used_dict.setdefault(k, 0)
                    if old_data and old_data.data:
                        places_used_dict[k] -= old_data.data.get(k, 0)
                    places_used_dict[k] += field.data[k]
                    if places_limit and (places_limit - places_used_dict.get(k, 0)) < 0:
                        raise ValidationError(_('No places left for the option: {0}').format(captions[k]))
        return [_check_number_of_places]

    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        unversioned_data, versioned_data = super(ChoiceBaseField, cls).process_field_data(data, old_data,
                                                                                          old_versioned_data)
        items = [x for x in versioned_data['choices'] if not x.get('remove')]
        captions = dict(old_data['captions']) if old_data is not None else {}
        if cls.has_default_item:
            unversioned_data.setdefault('default_item', None)
        for item in items:
            if 'id' not in item:
                item['id'] = unicode(uuid4())
            item.setdefault('is_billable', False)
            item['price'] = float(item['price']) if item.get('price') else 0
            item['places_limit'] = int(item['places_limit']) if item.get('places_limit') else 0
            item['max_extra_slots'] = int(item['max_extra_slots']) if item.get('max_extra_slots') else 0
            if cls.has_default_item and unversioned_data['default_item'] in {item['caption'], item['id']}:
                unversioned_data['default_item'] = item['id']
            captions[item['id']] = item.pop('caption')
        versioned_data['choices'] = items
        unversioned_data['captions'] = captions
        return unversioned_data, versioned_data

    def get_places_used(self):
        places_used = Counter()
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
        billable_choices = [x for x in versioned_data['choices'] if x['id'] in reg_data and x['is_billable']]
        price = 0
        for billable_field in billable_choices:
            price += billable_field['price']
            if billable_field.get('extra_slots_pay'):
                price += (reg_data[billable_field['id']] - 1) * billable_field['price']
        return price


class SingleChoiceField(ChoiceBaseField):
    name = 'single_choice'
    has_default_item = True

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

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        if not registration_data.data:
            return ''
        uuid, number_of_slots = registration_data.data.items()[0]
        caption = registration_data.field_data.field.data['captions'][uuid]
        return '{} (+{})'.format(caption, number_of_slots - 1) if number_of_slots > 1 else caption

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False, new_data_version=None):
        if billable_items_locked and old_data.price:
            # if the old field was paid we can simply ignore any change and keep the old value
            return {}
        # always store no-option as empty dict
        if value is None:
            value = {}
        return super(SingleChoiceField, self).process_form_data(registration, value, old_data, billable_items_locked,
                                                                new_data_version)


def _hashable_choice(choice):
    return frozenset(choice.iteritems())


class MultiChoiceField(ChoiceBaseField):
    name = 'multi_choice'

    @property
    def default_value(self):
        return {}

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        def _format_item(uuid, number_of_slots):
            caption = self.form_item.data['captions'][uuid]
            return '{} (+{})'.format(caption, number_of_slots - 1) if number_of_slots > 1 else caption

        reg_data = registration_data.data
        if not reg_data:
            return ''
        choices = sorted(_format_item(uuid, number_of_slots) for uuid, number_of_slots in reg_data.iteritems())
        return ', '.join(choices) if for_humans or for_search else choices

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False, new_data_version=None):
        # always store no-option as empty dict
        if value is None:
            value = {}

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
            selected_choice_hashes = set(selected_choice_hashes.itervalues())
            existing_version_hashes = {c['id']: _hashable_choice(c)
                                       for c in old_data.field_data.versioned_data['choices']}
            latest_version_hashes = {c['id']: _hashable_choice(c) for c in self.form_item.versioned_data['choices']}
            deselected_ids = old_data.data.viewkeys() - value.viewkeys()
            modified_deselected = any(latest_version_hashes.get(id_) != existing_version_hashes.get(id_)
                                      for id_ in deselected_ids)
            if selected_choice_hashes <= set(latest_version_hashes.itervalues()):
                # all choices available in the latest version - upgrade to that version
                return_value['field_data'] = self.form_item.current_data
            elif not modified_deselected and selected_choice_hashes <= set(existing_version_hashes.itervalues()):
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
            processed_data = super(MultiChoiceField, self).process_form_data(registration, value, old_data, False,
                                                                             return_value.get('field_data'))
            return {key: return_value.get(key, value) for key, value in processed_data.iteritems()}
        # XXX: This code still relies on the client sending data for the disabled fields.
        # This is pretty ugly but especially in case of non-billable extra slots it makes
        # sense to keep it like this.  If someone tampers with the list of billable fields
        # we detect it any reject the change to the field's data anyway.
        if has_old_data:
            old_choices_mapping = {x['id']: x for x in old_data.field_data.versioned_data['choices']}
            new_choices_mapping = {x['id']: x for x in new_choices}
            old_billable = {uuid: num for uuid, num in old_data.data.iteritems()
                            if old_choices_mapping[uuid]['is_billable'] and old_choices_mapping[uuid]['price']}
            new_billable = {uuid: num for uuid, num in value.iteritems()
                            if new_choices_mapping[uuid]['is_billable'] and new_choices_mapping[uuid]['price']}
        if has_old_data and old_billable != new_billable:
            # preserve existing data
            return return_value
        else:
            # nothing price-related changed
            # TODO: check item prices (in case there's a change between old/new version)
            # for now we simply ignore field changes in this case (since the old/new price
            # check in the base method will fail)
            processed_data = super(MultiChoiceField, self).process_form_data(registration, value, old_data, True,
                                                                             return_value.get('field_data'))
            return {key: return_value.get(key, value) for key, value in processed_data.iteritems()}


def _to_machine_date(date):
    return datetime.strptime(date, '%d/%m/%Y').strftime('%Y-%m-%d')


def _to_date(date):
    return datetime.strptime(date, '%Y-%m-%d').date()


class AccommodationField(RegistrationFormBillableItemsField):
    name = 'accommodation'
    wtf_field_class = JSONField
    versioned_data_fields = RegistrationFormBillableField.versioned_data_fields | {'choices'}

    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        unversioned_data, versioned_data = super(AccommodationField, cls).process_field_data(data, old_data,
                                                                                             old_versioned_data)
        items = [x for x in versioned_data['choices'] if not x.get('remove')]
        captions = dict(old_data['captions']) if old_data is not None else {}
        for item in items:
            if 'id' not in item:
                item['id'] = unicode(uuid4())
            item.setdefault('is_billable', False)
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
        arrival_date_from = _to_date(unversioned_data['arrival_date_from'])
        arrival_date_to = _to_date(unversioned_data['arrival_date_to'])
        departure_date_from = _to_date(unversioned_data['departure_date_from'])
        departure_date_to = _to_date(unversioned_data['departure_date_to'])
        data['arrival_dates'] = [(dt.date().isoformat(), format_date(dt))
                                 for dt in iterdays(arrival_date_from, arrival_date_to)]
        data['departure_dates'] = [(dt.date().isoformat(), format_date(dt))
                                   for dt in iterdays(departure_date_from, departure_date_to)]
        items = deepcopy(versioned_data['choices'])
        for item in items:
            item['caption'] = unversioned_data['captions'][item['id']]
        data['choices'] = items
        return data

    @property
    def validators(self):
        def _stay_dates_valid(form, field):
            if not field.data:
                return
            data = snakify_keys(field.data)
            if not data.get('is_no_accommodation'):
                try:
                    arrival_date = data['arrival_date']
                    departure_date = data['departure_date']
                except KeyError:
                    raise ValidationError(_("Arrival/departure date is missing"))
                if _to_date(arrival_date) > _to_date(departure_date):
                    raise ValidationError(_("Arrival date can't be set after the departure date."))

        def _check_number_of_places(form, field):
            if not field.data:
                return
            if form.modified_registration:
                old_data = form.modified_registration.data_by_field.get(self.form_item.id)
                if not old_data or not self.has_data_changed(snakify_keys(field.data), old_data):
                    return
            item = next((x for x in self.form_item.versioned_data['choices'] if x['id'] == field.data['choice']),
                        None)
            captions = self.form_item.data['captions']
            places_used_dict = self.get_places_used()
            if (item and item['places_limit'] and
                    (item['places_limit'] < places_used_dict.get(field.data['choice'], 0))):
                raise ValidationError(_("Not enough rooms in '{0}'").format(captions[item['id']]))
        return [_stay_dates_valid, _check_number_of_places]

    @property
    def view_data(self):
        return dict(super(AccommodationField, self).view_data, places_used=self.get_places_used())

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        friendly_data = dict(registration_data.data)
        if not friendly_data:
            return '' if for_humans or for_search else {}
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
        item = next((x for x in versioned_data['choices']
                     if reg_data['choice'] == x['id'] and x.get('is_billable', False)), None)
        if not item or not item['price']:
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
                data.update({'arrival_date': value['arrivalDate'],
                             'departure_date': value['departureDate']})
        return super(AccommodationField, self).process_form_data(registration, data, old_data, billable_items_locked,
                                                                 new_data_version)

    def get_places_used(self):
        places_used = Counter()
        for registration in self.form_item.registration_form.active_registrations:
            if self.form_item.id not in registration.data_by_field:
                continue
            data = registration.data_by_field[self.form_item.id].data
            if not data:
                continue
            places_used.update((data['choice'],))
        return dict(places_used)

    def iter_placeholder_info(self):
        yield 'name', 'Accommodation name for "{}" ({})'.format(self.form_item.title, self.form_item.parent.title)
        yield 'nights', 'Number of nights for "{}" ({})'.format(self.form_item.title, self.form_item.parent.title)
        yield 'arrival', 'Arrival date for "{}" ({})'.format(self.form_item.title, self.form_item.parent.title)
        yield 'departure', 'Departure date for "{}" ({})'.format(self.form_item.title, self.form_item.parent.title)

    def render_placeholder(self, data, key=None):
        mapping = {'name': 'choice',
                   'nights': 'nights',
                   'arrival': 'arrival_date',
                   'departure': 'departure_date'}
        rv = self.get_friendly_data(data).get(mapping[key], '')
        if isinstance(rv, date):
            rv = format_date(rv).decode('utf-8')
        return rv
