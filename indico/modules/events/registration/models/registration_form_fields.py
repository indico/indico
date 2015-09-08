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

from indico.core.db import db
from indico.modules.events.registration.models.items import RegistrationFormItemType, RegistrationFormItem
from indico.util.string import return_ascii


class RegistrationFormField(RegistrationFormItem):
    __mapper_args__ = {
        'polymorphic_identity': RegistrationFormItemType.field
    }

    # relationship backrefs
    # - data (RegistrationFormFieldData.field)

    @return_ascii
    def __repr__(self):
        return '<RegistrationFormField({}, {})>'.format(self.id, self.registration_form_id)


class RegistrationFormFieldData(db.Model):
    __tablename__ = 'registration_form_field_data'
    __table_args__ = {'schema': 'event_registration'}

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
    # TODO: which data? price, limit, options, etc.

    field = db.relationship(
        'RegistrationFormField',
        # XXX: do we want it lazy?
        lazy=True,
        backref=db.backref(
            'data',
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    # relationship backref
    # - registration_data (RegistrationData.field_data)

    @return_ascii
    def __repr__(self):
        return '<RegistrationFormFieldData({}, {})>'.format(self.id, self.field_id)
