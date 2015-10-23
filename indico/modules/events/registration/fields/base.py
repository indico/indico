# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

    def calculate_price(self, registration_data):
        """Calculates the price of the field given the registration data"""
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

    def save_data(self, registration, value):
        registration.data.append(RegistrationData(field_data=self.form_item.current_data, data=value))

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

    @property
    def view_data(self):
        return {}

    def get_friendly_data(self, registration_data):
        return registration_data.data


class RegistrationFormBillableField(RegistrationFormFieldBase):
    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        data = deepcopy(data)
        data.setdefault('is_billable', False)
        data['price'] = float(data['price']) if data.get('price') else 0
        return super(RegistrationFormBillableField, cls).process_field_data(data, old_data, old_versioned_data)

    def calculate_price(self, registration_data):
        data = registration_data.field_data.versioned_data
        return data.get('price', 0) if data.get('is_billable') else 0


class RegistrationFormBillableItemsField(RegistrationFormBillableField):
    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        unversioned_data, versioned_data = super(RegistrationFormBillableItemsField, cls).process_field_data(
            data, old_data, old_versioned_data)
        # we don't have field-level billing data here
        del versioned_data['is_billable']
        del versioned_data['price']
        return unversioned_data, versioned_data

    def calculate_price(self, registration_data):
        # billable items need custom logic
        raise NotImplementedError
