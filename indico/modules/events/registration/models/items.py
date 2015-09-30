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
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.registration.fields import get_field_types
from indico.util.string import return_ascii, camelize_keys
from indico.util.struct.enum import IndicoEnum


def _get_next_position(context):
    """Get the next position for a form item."""
    regform_id = context.current_parameters['registration_form_id']
    parent_id = context.current_parameters['parent_id']
    res = (db.session.query(db.func.max(RegistrationFormItem.position))
           .filter_by(parent_id=parent_id, registration_form_id=regform_id, is_deleted=False)
           .one())
    return (res[0] or 0) + 1


class RegistrationFormItemType(int, IndicoEnum):
    section = 1
    field = 2
    text = 3


class RegistrationFormItem(db.Model):
    __tablename__ = 'form_items'
    __table_args__ = (db.CheckConstraint("(input_type IS NULL) = (type = {type})"
                                         .format(type=RegistrationFormItemType.section), name='valid_input'),
                      {'schema': 'event_registration'})
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
        db.ForeignKey('event_registration.forms.id'),
        index=True,
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
        db.ForeignKey('event_registration.form_items.id'),
        index=True,
        nullable=True
    )
    position = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_position
    )
    #: The title of this field
    title = db.Column(
        db.String,
        nullable=False
    )
    #: Description of this field
    description = db.Column(
        db.String,
        nullable=True
    )
    #: Whether the field is enabled
    is_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: Whether field has been "deleted"
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: determines if the field is mandatory
    is_required = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: input type of this field
    input_type = db.Column(
        db.String,
        nullable=True
    )
    #: unversioned field data
    data = db.Column(
        JSON,
        nullable=False
    )

    #: The ID of the latest data
    current_data_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.form_field_data.id', use_alter=True),
        index=True,
        nullable=True
    )

    #: The latest value of the field
    current_data = db.relationship(
        'RegistrationFormFieldData',
        primaryjoin='RegistrationFormItem.current_data_id == RegistrationFormFieldData.id',
        foreign_keys=current_data_id,
        lazy=True,
        post_update=True
    )

    #: The list of all versions of the field data
    data_versions = db.relationship(
        'RegistrationFormFieldData',
        primaryjoin='RegistrationFormItem.id == RegistrationFormFieldData.field_id',
        foreign_keys='RegistrationFormFieldData.field_id',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'field',
            lazy=False
        )
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

    # The children of the item and the parent backref
    children = db.relationship(
        'RegistrationFormItem',
        lazy=True,
        order_by='RegistrationFormItem.position',
        backref=db.backref(
            'parent',
            lazy=False,
            remote_side=[id]
        )
    )

    @property
    def view_data(self):
        """Returns object with data that Angular can understand"""
        return dict(id=self.id, description=self.description, lock=[])

    @property
    def wtf_field(self):
        return get_field_types()[self.input_type](self)

    @property
    def is_section(self):
        return self.type == RegistrationFormItemType.section

    @return_ascii
    def __repr__(self):
        return '<{}({})>'.format(type(self).__name__, self.id)


class RegistrationFormSection(RegistrationFormItem):
    __mapper_args__ = {
        'polymorphic_identity': RegistrationFormItemType.section
    }

    @property
    def locator(self):
        return dict(self.registration_form.locator, section_id=self.id)

    @property
    def view_data(self):
        field_data = dict(super(RegistrationFormSection, self).view_data, enabled=self.is_enabled,
                          title=self.title, items=[child.view_data for child in self.children
                                                   if not child.is_deleted])
        return camelize_keys(field_data)


class RegistrationFormText(RegistrationFormItem):
    __mapper_args__ = {
        'polymorphic_identity': RegistrationFormItemType.text
    }

    @property
    def locator(self):
        return dict(self.parent.locator, field_id=self.id)

    @property
    def view_data(self):
        field_data = dict(super(RegistrationFormText, self).view_data, disabled=not self.is_enabled,
                          input=self.input_type, caption=self.title, **self.current_data.versioned_data)
        return camelize_keys(field_data)
