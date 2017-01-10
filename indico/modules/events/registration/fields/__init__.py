# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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


def get_field_types():
    """Get a dict with all registration field types"""
    from .simple import (TextField, NumberField, TextAreaField, CheckboxField, DateField, BooleanField, PhoneField,
                         CountryField, FileField, EmailField)
    from .choices import SingleChoiceField, AccommodationField, MultiChoiceField
    return {field.name: field for field in (TextField, NumberField, TextAreaField, SingleChoiceField, CheckboxField,
                                            DateField, BooleanField, PhoneField, CountryField, FileField, EmailField,
                                            AccommodationField, MultiChoiceField)}
