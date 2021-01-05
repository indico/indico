# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from copy import deepcopy

from wtforms.fields import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget


class FieldConfigForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()], description=_("The title of the field"))
    description = TextAreaField(_('Description'), description=_("The description of the field"))
    is_required = BooleanField(_('Required'), widget=SwitchWidget(),
                               description=_("Whether the user has to fill out the field"))


class BaseField(object):
    """Base class for a custom field.

    To create a new field, subclass this class and register
    it using the `get_fields` signal.

    :param obj: The object associated with the field.
    """

    #: unique name of the field type
    name = None
    #: plugin containing this field type - assigned automatically
    plugin = None
    #: displayed name of the field type
    friendly_name = None
    #: wtform field class for this field
    wtf_field_class = None
    #: the base class for the config form
    config_form_base = FieldConfigForm
    #: the WTForm used to configure the field. this must not be an
    #: actual `Form` subclass but just a regular object containing
    #: fields.  it will be mixed into `config_form_base` to create
    #: the actual form.
    config_form = None
    #: the validator to use if the field is required
    required_validator = DataRequired
    #: the validator to use if the field is not required
    not_required_validator = Optional
    #: the common settings stored on the object itself instead of
    #: the `field_data` json structure.  this also specifies the
    #: order of those fields in the config form.
    common_settings = ('title', 'description', 'is_required')

    def __init__(self, obj):
        self.object = obj

    @property
    def validators(self):
        """Return a list of validators for this field."""
        return None

    @property
    def wtf_field_kwargs(self):
        """Return a dict of kwargs for this field's wtforms field."""
        return {}

    def create_wtf_field(self):
        """Return a WTForms field for this field."""
        return self._make_wtforms_field(self.wtf_field_class, self.validators, **self.wtf_field_kwargs)

    @classmethod
    def create_config_form(cls, *args, **kwargs):
        """Create the WTForm to configure this field."""
        bases = (cls.config_form_base, cls.config_form) if cls.config_form is not None else (cls.config_form_base,)
        form_cls = type(b'_FieldConfigForm', bases, {})
        form = form_cls(*args, **kwargs)
        form._common_fields = cls.common_settings
        return form

    def copy_field_data(self):
        """Return a copy of the field's configuration data."""
        return deepcopy(self.object.field_data)

    def is_value_empty(self, value):
        """Check whether the stored value is considered empty.

        :param value: The database object containing the value of
                      the field
        """
        return value.data is None

    def update_object(self, data):
        """Update the object containing this field.

        :param data: A dict containing already validated data from
                     form submission.
        """
        for field in self.common_settings:
            setattr(self.object, field, data[field])
        self.object.field_type = self.name
        self.object.field_data = {name: value
                                  for name, value in data.iteritems()
                                  if name not in self.common_settings and name != 'csrf_token'}

    def get_friendly_value(self, value):
        """Return the human-friendly version of the field's value.

        :param value: The database object containing the value of
                      the field
        """
        return value if value is not None else ''

    def _make_wtforms_field(self, field_cls, validators=None, **kwargs):
        """Util to instantiate a WTForms field.

        This creates a field with the proper title, description and
        if applicable a DataRequired validator.

        :param field_cls: A WTForms field class
        :param validators: A list of additional validators
        :param kwargs: kwargs passed to the field constructor
        """
        validators = list(validators) if validators is not None else []
        if self.object.is_required:
            validators.append(self.required_validator())
        elif self.not_required_validator:
            validators.append(self.not_required_validator())
        return field_cls(self.object.title, validators, description=self.object.description, **kwargs)
