# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.event import listens_for
from werkzeug.datastructures import ImmutableDict

from indico.core.db import db
from indico.modules.events.registration.fields import get_field_types
from indico.modules.events.registration.models.items import RegistrationFormItem, RegistrationFormItemType
from indico.util.string import camelize_keys, return_ascii


class RegistrationFormFieldData(db.Model):
    """Description of a registration form field."""

    __tablename__ = 'form_field_data'
    __table_args__ = {'schema': 'event_registration'}

    #: The ID of the object
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the registration form field
    field_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.form_items.id'),
        index=True,
        nullable=False
    )
    #: Data describing the field
    versioned_data = db.Column(
        JSONB,
        nullable=False
    )

    # relationship backrefs:
    # - field (RegistrationFormItem.data_versions)
    # - registration_data (RegistrationData.field_data)

    @return_ascii
    def __repr__(self):
        return '<RegistrationFormFieldData({}, {})>'.format(self.id, self.field_id)


class RegistrationFormField(RegistrationFormItem):
    """A registration form field."""

    __mapper_args__ = {
        'polymorphic_identity': RegistrationFormItemType.field
    }

    @property
    def locator(self):
        return dict(self.parent.locator, field_id=self.id)

    @property
    def field_impl(self):
        """Gets the implementation of the field.

        :return: An instance of a `RegistrationFormFieldBase` subclass
        """
        return get_field_types()[self.input_type](self)

    @property
    def versioned_data(self):
        return ImmutableDict(self.current_data.versioned_data) if self.current_data is not None else None

    @versioned_data.setter
    def versioned_data(self, value):
        if self.current_data is not None and value == self.current_data.versioned_data:
            return
        # create new version if the current one is associated with anything
        if self.current_data is None or self.current_data.registration_data:
            self.current_data = RegistrationFormFieldData(versioned_data=value)
        else:
            self.current_data.versioned_data = value

    @property
    def view_data(self):
        base_dict = dict(self.versioned_data, **self.data)
        base_dict.update(is_enabled=self.is_enabled, title=self.title, is_required=self.is_required,
                         input_type=self.input_type, html_name=self.html_field_name,
                         **super(RegistrationFormField, self).view_data)
        base_dict.update(self.field_impl.view_data)
        return camelize_keys(base_dict)

    @property
    def html_field_name(self):
        return 'field_{}'.format(self.id)

    def get_friendly_data(self, registration_data, **kwargs):
        return self.field_impl.get_friendly_data(registration_data, **kwargs)

    def calculate_price(self, registration_data):
        return self.field_impl.calculate_price(registration_data.data, registration_data.field_data.versioned_data)


class RegistrationFormPersonalDataField(RegistrationFormField):
    __mapper_args__ = {
        'polymorphic_identity': RegistrationFormItemType.field_pd
    }

    @property
    def view_data(self):
        data = dict(super(RegistrationFormPersonalDataField, self).view_data,
                    field_is_required=self.personal_data_type.is_required,
                    field_is_personal_data=True)
        return camelize_keys(data)

    @property
    def html_field_name(self):
        return self.personal_data_type.name


@listens_for(RegistrationFormField.current_data, 'set')
@listens_for(RegistrationFormPersonalDataField.current_data, 'set')
def _add_current_data(target, value, *unused):
    if value is None:
        raise ValueError('current_data cannot be set to None')
    with db.session.no_autoflush:
        target.data_versions.append(value)
