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

from sqlalchemy.dialects.postgresql import JSON

from indico.core.db import db
from indico.modules.events.registration.models.items import RegistrationFormItemType, RegistrationFormItem
from indico.util.string import return_ascii
from MaKaC.webinterface.common.countries import CountryHolder


class RegistrationFormFieldData(db.Model):
    __tablename__ = 'registration_form_field_data'
    __table_args__ = (
        db.CheckConstraint("(input_type IS NULL) = (type = {type})"
                           .format(type=RegistrationFormItemType.section), name='valid_input'),
        {'schema': 'event_registration'}
    )

    #: The ID of the object
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the registration form field
    field_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.registration_form_items.id')
    )
    #: Data describing the field
    versioned_data = db.Column(
        JSON,
        nullable=False
    )

    # relationship backref
    # - registration_data (RegistrationData.field_data)

    @return_ascii
    def __repr__(self):
        return '<RegistrationFormFieldData({}, {})>'.format(self.id, self.field_id)


class RegistrationFormField(RegistrationFormItem):
    __mapper_args__ = {
        'polymorphic_identity': RegistrationFormItemType.field
    }

    #: determines if the field is mandatory
    is_required = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    @property
    def locator(self):
        return dict(self.parent.locator, field_id=self.id)

    @property
    def view_data(self):
        base_dict = dict(self.current_data.versioned_data)
        base_dict.update(disabled=not self.is_enabled, caption=self.title, mandatory=self.is_required,
                         input=self.input_type, **super(RegistrationFormField, self).view_data)
        if self.input_type == 'country':
            base_dict['radioitems'] = []
            for key, val in CountryHolder.getCountries().iteritems():
                base_dict['radioitems'].append({'caption': val, 'countryKey': key})
        return base_dict

    @return_ascii
    def __repr__(self):
        return '<RegistrationFormField({}, {})>'.format(self.id, self.registration_form_id)
