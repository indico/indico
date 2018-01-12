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

from copy import deepcopy

from wtforms.validators import DataRequired, Optional

from indico.modules.events.registration.models.registrations import RegistrationData


class RegistrationFormFieldBase(object):
    """Base class for a registration form field definition"""

    #: unique name of the field type
    name = None
    #: wtform field class
    wtf_field_class = None
    #: additional options for the WTForm class
    wtf_field_kwargs = {}
    #: the validator to use when the field is required
    required_validator = DataRequired
    #: the validator to use when the field is not required
    not_required_validator = Optional
    #: the data fields that need to be versioned
    versioned_data_fields = frozenset({'is_billable', 'price'})

    def __init__(self, form_item):
        self.form_item = form_item

    @property
    def default_value(self):
        return ''

    @property
    def validators(self):
        """Returns a list of validators for this field"""
        return None

    @property
    def filter_choices(self):
        return None

    def calculate_price(self, reg_data, versioned_data):
        """Calculates the price of the field

        :param reg_data: The user data for the field
        :param versioned_data: The versioned field data to use
        """
        return 0

    def create_sql_filter(self, data_list):
        """
        Creates a SQL criterion to check whether the field's value is
        in `data_list`.  The function is expected to return an
        operation on ``Registrationdata.data``.
        """
        return RegistrationData.data.op('#>>')('{}').in_(data_list)

    def create_wtf_field(self):
        validators = list(self.validators) if self.validators is not None else []
        if self.form_item.is_required:
            validators.append(self.required_validator())
        elif self.not_required_validator:
            validators.append(self.not_required_validator())
        return self.wtf_field_class(self.form_item.title, validators, **self.wtf_field_kwargs)

    def has_data_changed(self, value, old_data):
        return value != old_data.data

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False):
        """Convert form data into database-usable dictionary.

        :param registration: The registration the data is used for
        :param value: The value from the WTForm
        :param old_data: The existing `RegistrationData` in case a
                         registration is being modified.
        :param billable_items_locked: Whether modifications to any
                                      billable item should be ignored.
        """

        if old_data is not None and not self.has_data_changed(value, old_data):
            return {}
        else:
            return {
                'field_data': self.form_item.current_data,
                'data': value
            }

    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        """Processes the settings of the field.

        :param data: The field data from the client
        :param old_data: The old unversioned field data (if available)
        :param old_versioned_data: The old versioned field data (if
                                   available)
        :return: A ``(unversioned_data, versioned_data)`` tuple
        """
        data = dict(data)
        if 'places_limit' in data:
            data['places_limit'] = int(data['places_limit']) if data['places_limit'] else 0
        versioned_data = {k: v for k, v in data.iteritems() if k in cls.versioned_data_fields}
        unversioned_data = {k: v for k, v in data.iteritems() if k not in cls.versioned_data_fields}
        return unversioned_data, versioned_data

    @classmethod
    def unprocess_field_data(cls, versioned_data, unversioned_data):
        return dict(versioned_data, **unversioned_data)

    @property
    def view_data(self):
        return self.unprocess_field_data(self.form_item.versioned_data, self.form_item.data)

    def get_friendly_data(self, registration_data, for_humans=False):
        """Return the data contained in the field

        If for_humans is True, return a human-readable string representation.
        """
        return registration_data.data

    def iter_placeholder_info(self):
        yield None, 'Value of "{}" ({})'.format(self.form_item.title, self.form_item.parent.title)

    def render_placeholder(self, data, key=None):
        return self.get_friendly_data(data)

    def get_places_used(self):
        """Returns the number of used places for the field"""
        return 0


class RegistrationFormBillableField(RegistrationFormFieldBase):
    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        data = deepcopy(data)
        data.setdefault('is_billable', False)
        data['price'] = float(data['price']) if data.get('price') else 0
        return super(RegistrationFormBillableField, cls).process_field_data(data, old_data, old_versioned_data)

    def calculate_price(self, reg_data, versioned_data):
        return versioned_data.get('price', 0) if versioned_data.get('is_billable') else 0

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False, new_data_version=None):
        if new_data_version is None:
            new_data_version = self.form_item.current_data
        if billable_items_locked and old_data.price != self.calculate_price(value, new_data_version.versioned_data):
            return {}
        return super(RegistrationFormBillableField, self).process_form_data(registration, value, old_data)


class RegistrationFormBillableItemsField(RegistrationFormBillableField):
    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        unversioned_data, versioned_data = super(RegistrationFormBillableItemsField, cls).process_field_data(
            data, old_data, old_versioned_data)
        # we don't have field-level billing data here
        del versioned_data['is_billable']
        del versioned_data['price']
        return unversioned_data, versioned_data

    def calculate_price(self, reg_data, versioned_data):
        # billable items need custom logic
        raise NotImplementedError
