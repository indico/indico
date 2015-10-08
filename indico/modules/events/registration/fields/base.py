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

from wtforms.validators import DataRequired, Optional

from indico.modules.events.registration.models.registrations import RegistrationData


class RegistrationFormFieldBase(object):
    """Base class for a registration form field definition"""

    #: unique name of the field type
    name = None
    #: wtform field class
    wtf_field_class = None
    #: the validator to use when the field is required
    required_validator = DataRequired
    #: the validator to use when the field is not required
    not_required_validator = Optional
    #: additional options for the WTForm class
    field_kwargs = {}

    def __init__(self, form_item):
        self.form_item = form_item

    @property
    def validators(self):
        """Returns a list of validators for this field"""
        return None

    def create_wtf_field(self):
        validators = list(self.validators) if self.validators is not None else []
        if self.form_item.current_data.versioned_data.get('is_required'):
            validators.append(self.required_validator())
        elif self.not_required_validator:
            validators.append(self.not_required_validator())
        return self.wtf_field_class(self.form_item.title, validators, **self.field_kwargs)

    def save_data(self, registration, value):
        registration.data.append(RegistrationData(field_data_id=self.form_item.current_data_id, data=value))

    @classmethod
    def modify_post_data(cls, post_data):
        pass

    @property
    def default_value(self):
        return ''
