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
from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.string import return_ascii
from indico.util.struct.enum import IndicoEnum


class RegistrationFormItemType(int, IndicoEnum):
    section = 1
    field = 2
    text = 3


class RegistrationFormItem(db.Model):
    __tablename__ = 'registration_form_items'
    __table_args__ = {'schema': 'event_registration'}
    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': None
    }

    #: The ID of the object
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID  of the registration form
    registration_form_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.registration_forms.id'),
        nullable=False
    )
    #: The type of the registration form item
    type = db.Column(
        PyIntEnum(RegistrationFormItemType),
        nullable=False
    )
    #: The ID of the parent form item
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.registration_form_items.id'),
        nullable=True
    )
    position = db.Column(
        db.Integer,
        nullable=False
        # TODO: default=_get_next_position
    )

    # The registration form
    registration_form = db.relationship(
        'RegistrationForm',
        lazy=True,
        backref=db.backref(
            'form_items',
            lazy=True,
            cascade='all, delete-orphan'
        )
    )

    # The parent of the item and the children backref
    parent = db.relationship(
        'RegistrationFormItem',
        lazy=True,
        backref=db.backref(
            'children',
            lazy=False,
            remote_side=[id]
        )
    )

    @return_ascii
    def __repr__(self):
        return '<{}({}, {})>'.format(type(self).__name__, self.id)


class RegistrationFormSection(RegistrationFormItem):
    __mapper_args__ = {
        'polymorphic_identity': RegistrationFormItemType.section
    }


class RegistrationFormText(RegistrationFormItem):
    __mapper_args__ = {
        'polymorphic_identity': RegistrationFormItemType.text
    }
