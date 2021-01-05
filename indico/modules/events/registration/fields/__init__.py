# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

def get_field_types():
    """Get a dict with all registration field types."""
    from .choices import AccommodationField, MultiChoiceField, SingleChoiceField
    from .simple import (BooleanField, CheckboxField, CountryField, DateField, EmailField, FileField, NumberField,
                         PhoneField, TextAreaField, TextField)
    return {field.name: field for field in (TextField, NumberField, TextAreaField, SingleChoiceField, CheckboxField,
                                            DateField, BooleanField, PhoneField, CountryField, FileField, EmailField,
                                            AccommodationField, MultiChoiceField)}
