# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core import signals
from indico.modules.events.registration.fields.base import RegistrationFormFieldBase
from indico.web.fields import get_field_definitions


def get_field_types():
    """Get a dict with all registration field types."""
    return get_field_definitions(RegistrationFormFieldBase)


@signals.core.get_fields.connect_via(RegistrationFormFieldBase)
def _get_fields(sender, **kwargs):
    from .accompanying import AccompanyingPersonsField
    from .choices import AccommodationField, MultiChoiceField, SingleChoiceField
    from .sessions import SessionsField
    from .simple import (BooleanField, CheckboxField, CountryField, DateField, EmailField, FileField, NumberField,
                         PhoneField, PictureField, TextAreaField, TextField)
    yield AccommodationField
    yield MultiChoiceField
    yield SingleChoiceField
    yield AccompanyingPersonsField
    yield BooleanField
    yield CheckboxField
    yield CountryField
    yield DateField
    yield EmailField
    yield FileField
    yield NumberField
    yield PhoneField
    yield TextAreaField
    yield TextField
    yield PictureField
    yield SessionsField


@signals.core.app_created.connect
def _check_field_definitions(app, **kwargs):
    # This will raise RuntimeError if the field names are not unique
    get_field_types()
