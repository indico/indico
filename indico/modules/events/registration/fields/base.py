# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from copy import deepcopy
from decimal import Decimal

from markupsafe import Markup
from marshmallow import fields, validate

from indico.core.marshmallow import mm
from indico.modules.events.registration.custom import RegistrationListColumn
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.util.i18n import _
from indico.util.marshmallow import not_empty


class FieldSetupSchemaBase(mm.Schema):
    """Base schema for configuring registration form fields.

    Any global options that go into every field's JSON config data can be
    added here; if the options are stored in a dedicated column, they should
    go to `GeneralFieldDataSchema` instead.
    """


class BillableFieldDataSchema(FieldSetupSchemaBase):
    """Base config schema for fields that can have a price."""

    price = fields.Float(load_default=0)


class LimitedPlacesBillableFieldDataSchema(BillableFieldDataSchema):
    """Base config schema for fields that can have a price and limited places."""

    places_limit = fields.Integer(load_default=0, validate=validate.Range(0))


class LimitedPlacesBillableItemSchema(LimitedPlacesBillableFieldDataSchema):
    """Base config schema for field items that can have a price and limited places."""


class RegistrationFormFieldBase:
    """Base class for a registration form field definition."""

    #: unique name of the field type
    name = None
    #: the data fields that need to be versioned
    versioned_data_fields = frozenset({'price'})
    #: the marshmallow field class for regform submission
    mm_field_class = None
    #: positional arguments for the marshmallow field
    mm_field_args = ()
    #: additional options for the marshmallow field
    mm_field_kwargs = {}
    #: the marshmallow base schema for configuring the field
    setup_schema_base_cls = FieldSetupSchemaBase
    #: a dict with extra marshmallow fields to include in the setup schema
    setup_schema_fields = {}
    #: whether this field is associated with a file instead of normal data
    is_file_field = False
    #: whether this field is invalid and cannot be used
    is_invalid_field = False
    #: whether this field must not be "empty" (falsy value) if required
    not_empty_if_required = True
    #: whether this field may be used as a condition; this is purely for validation,
    #: on the frontend it depends solely on the config in the field registry whether
    #: the field can be selected as a condition.
    allow_condition = False

    def __init__(self, form_item):
        self.form_item = form_item

    @property
    def default_value(self):
        """A default value to store when the field does not have a real value.

        This is used e.g. for manager-only fields when a user registers, when purging
        a field's data, or when generating the preview for a notification email.

        This may return `NotImplemented` to indicate that no default value exists. In
        that case, it is mandatory to override `ui_default_value` and `empty_value`.
        """
        return ''

    @property
    def ui_default_value(self):
        """A default value that is passed to the registration form UI.

        For most fields this is the same as the `default_value`, but in some cases
        it may not be possible to get a valid default value to be used in the backend
        code or stored in the database; in that case the UI can use a more suitable
        default while the backend uses something else (or no value at all).
        """
        default = self.default_value
        assert default is not NotImplemented
        return default

    @property
    def empty_value(self):
        # This value is used when a manager edits an existing registration, and
        # it should be something that, especially in case of choice fields, does
        # not preselect any of the available choices (such as "no accommodation"
        # or whatever default value is set for a field).
        default = self.default_value
        assert default is not NotImplemented
        return default

    def get_data_for_condition(self, value) -> set:
        """Convert field value to the format expected in a condition check.

        If this field can be used for a condition, this method needs to return a
        set of values (based on the `value` the field currently contains). If this
        set intersects with the other field's configured condition, that field will
        be visible.

        The logic in this method must match the corresponding ``getDataForCondition``
        function in the frontend field registry.
        """
        raise NotImplementedError('Field cannot be used as a condition')

    def get_validators(self, existing_registration):
        """Return a list of marshmallow validators for this field.

        The ``existing_registration`` is ``None`` if the user is newly registering
        and not editing a registration.
        """
        return None

    @property
    def filter_choices(self):
        return None

    def calculate_price(self, reg_data, versioned_data):
        """Calculate the price of the field.

        :param reg_data: The user data for the field
        :param versioned_data: The versioned field data to use
        """
        return 0

    def create_sql_filter(self, data_list):
        """
        Create a SQL criterion to check whether the field's value is
        in `data_list`.  The function is expected to return an
        operation on ``Registrationdata.data``.
        """
        return RegistrationData.data.op('#>>')('{}').in_(data_list)

    def create_setup_schema(self, context=None):
        name = f'{type(self).__name__}SetupDataSchema'
        schema = self.setup_schema_base_cls.from_dict(self.setup_schema_fields, name=name)
        return schema(context=context)

    def create_mm_field(self, registration=None, override_required=False):
        """
        Create a marshmallow field.
        When modifying an existing registration, the `registration` parameter is
        the previous registration. We pass the registration because
        some field validators need the old data.

        :param registration: The previous registration if modifying an existing one, otherwise none
        """
        validators = self.get_validators(registration) or []
        if not isinstance(validators, list):
            validators = [validators]

        # Managers should be able to register without all required fields, but the personal data
        # fields are mandatory either way.
        from indico.modules.events.registration.models.form_fields import RegistrationFormPersonalDataField
        required_personal_field = (
            isinstance(self.form_item, RegistrationFormPersonalDataField) and
            self.form_item.personal_data_type.is_required
        )
        skip_required = override_required and not required_personal_field

        if self.form_item.is_required and self.not_empty_if_required and not skip_required:
            validators.append(not_empty)

        mm_field_kwargs = self.mm_field_kwargs
        if skip_required:
            mm_field_kwargs['allow_none'] = True

        return self.mm_field_class(*self.mm_field_args,
                                   required=(self.form_item.is_required and not skip_required),
                                   validate=validators,
                                   **mm_field_kwargs)

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
        """Process the settings of the field.

        :param data: The field data from the client
        :param old_data: The old unversioned field data (if available)
        :param old_versioned_data: The old versioned field data (if
                                   available)
        :return: A ``(unversioned_data, versioned_data)`` tuple
        """
        data = dict(data)
        versioned_data = {k: v for k, v in data.items() if k in cls.versioned_data_fields}
        unversioned_data = {k: v for k, v in data.items() if k not in cls.versioned_data_fields}
        return unversioned_data, versioned_data

    @classmethod
    def unprocess_field_data(cls, versioned_data, unversioned_data):
        return versioned_data | unversioned_data

    @property
    def view_data(self):
        return (self.unprocess_field_data(self.form_item.versioned_data, self.form_item.data) |
                {'default_value': self.ui_default_value, 'is_purged': self.form_item.is_purged})

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        """Return the data contained in the field.

        If for_humans is True, return a human-readable string representation.
        If for_search is True, return a string suitable for comparison in search.
        """
        return registration_data.data

    def iter_placeholder_info(self):
        yield None, _('Value of "{form_item}" ({parent_form_item})').format(
            form_item=self.form_item.title,
            parent_form_item=self.form_item.parent.title
        )

    def render_placeholder(self, data, key=None):
        return self.get_friendly_data(data)

    def get_places_used(self):
        """Return the number of used places for the field."""
        return 0

    def render_summary_data(self, data: RegistrationData) -> str | Markup:
        """Render the field's data in the registration summary."""
        return data.friendly_data

    def render_invoice_data(self, data: RegistrationData) -> str | Markup:
        """Render the field's data in the registration invoice."""
        return data.friendly_data

    def render_email_data(self, data: RegistrationData) -> str | Markup:
        """Render the field's data in a registration notification email.

        In case the field is being modified in an existing registration, this method
        is not called.
        """
        return data.friendly_data

    def render_email_diff_data(self, diff_data) -> str | Markup:
        """Render the field's data in a registraiton notification email.

        This method is called when an existing registration is being modified and
        the field already contained data. `diff_data` contains the value as returned
        by :meth:`get_snapshot_data`.
        """
        return diff_data

    def get_snapshot_data(self, data: RegistrationData):
        """Get the field's data for snapshotting.

        The snapshot is used to generate the diff view in notification emails, so
        this should usually use same format as :meth:`render_email_data.
        """
        return self.render_email_data(data)

    def render_reglist_column(self, data: RegistrationData) -> RegistrationListColumn:
        """Render the field's data in the management registration list table."""
        return RegistrationListColumn(data.friendly_data, data.search_data)

    def render_spreadsheet_data(self, data: RegistrationData):
        """Render the field's data in a spreadsheet.

        This may return any data type that's handled by Indico's spreadsheet utils.
        """
        return data.friendly_data


class RegistrationFormBillableField(RegistrationFormFieldBase):
    setup_schema_base_cls = BillableFieldDataSchema

    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        data = deepcopy(data)
        data['price'] = float(data['price']) if data.get('price') else 0
        return super().process_field_data(data, old_data, old_versioned_data)

    def calculate_price(self, reg_data, versioned_data):
        return Decimal(str(versioned_data.get('price', 0)))

    @classmethod
    def unprocess_field_data(cls, versioned_data, unversioned_data):
        return versioned_data | unversioned_data

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False, new_data_version=None):
        if new_data_version is None:
            new_data_version = self.form_item.current_data
        if billable_items_locked and old_data.price != self.calculate_price(value, new_data_version.versioned_data):
            return {}
        return super().process_form_data(registration, value, old_data)


class RegistrationFormBillableItemsField(RegistrationFormBillableField):
    setup_schema_base_cls = FieldSetupSchemaBase

    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        unversioned_data, versioned_data = super().process_field_data(
            data, old_data, old_versioned_data)
        # we don't have field-level billing data here
        del versioned_data['price']
        return unversioned_data, versioned_data

    def calculate_price(self, reg_data, versioned_data):
        # billable items need custom logic
        raise NotImplementedError


class InvalidRegistrationFormField(RegistrationFormFieldBase):
    """A field implementation for missing plugin fields."""

    is_invalid_field = True

    def create_mm_field(self, registration=None, override_required=False):
        return None
