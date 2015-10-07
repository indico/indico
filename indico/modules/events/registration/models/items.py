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

from uuid import uuid4

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.decorators import strict_classproperty
from indico.util.string import return_ascii, camelize_keys, format_repr
from indico.util.struct.enum import IndicoEnum

from MaKaC.webinterface.common.person_titles import TitlesRegistry


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
    section_pd = 4  # personal data section
    field_pd = 5  # personal data field


class PersonalDataType(int, IndicoEnum):
    email = 1
    first_name = 2
    last_name = 3
    affiliation = 4
    title = 5
    address = 6
    phone = 7

    @strict_classproperty
    @classmethod
    def FIELD_DATA(cls):
        title_item = {'price': 0,
                      'is_billable': False,
                      'places_limit': 0,
                      'is_enabled': True}
        return [
            (cls.title, {
                'title': 'Title',
                'input_type': 'radio',
                'data': {
                    'input_type': 'dropdown',
                    'with_extra_slots': False
                },
                'versioned_data': {
                    'radioitems': [dict(title_item, id=unicode(uuid4()), caption=t)
                                   for t in TitlesRegistry.getList() if t]
                }
            }),
            (cls.first_name, {
                'title': 'First Name',
                'input_type': 'text'
            }),
            (cls.last_name, {
                'title': 'Last Name',
                'input_type': 'text'
            }),
            (cls.email, {
                'title': 'Email Address',
                'input_type': 'email'
            }),
            (cls.affiliation, {
                'title': 'Affiliation',
                'input_type': 'text'
            }),
            (cls.address, {
                'title': 'Address',
                'input_type': 'textarea'
            }),
            (cls.phone, {
                'title': 'Phone Number',
                'input_type': 'phone'
            }),
        ]

    @property
    def is_required(self):
        return self in {PersonalDataType.email, PersonalDataType.first_name, PersonalDataType.last_name}

    @property
    def column(self):
        """
        The Registration column in which the value is stored in
        addition to the regular registration data entry.
        """
        if self in {PersonalDataType.email, PersonalDataType.first_name, PersonalDataType.last_name}:
            return self.name
        else:
            return None


class RegistrationFormItem(db.Model):
    __tablename__ = 'form_items'
    __table_args__ = (
        db.CheckConstraint("(input_type IS NULL) = (type NOT IN ({t.field}, {t.field_pd}))"
                           .format(t=RegistrationFormItemType),
                           name='valid_input'),
        db.CheckConstraint("NOT is_manager_only OR type = {type}".format(type=RegistrationFormItemType.section),
                           name='valid_manager_only'),
        db.CheckConstraint("(type IN ({t.section}, {t.section_pd})) = (parent_id IS NULL)"
                           .format(t=RegistrationFormItemType),
                           name='top_level_sections'),
        db.CheckConstraint("(type != {type}) = (personal_data_type IS NULL)"
                           .format(type=RegistrationFormItemType.field_pd),
                           name='pd_field_type'),
        db.CheckConstraint("NOT is_deleted OR (type NOT IN ({t.section_pd}, {t.field_pd}))"
                           .format(t=RegistrationFormItemType),
                           name='pd_not_deleted'),
        db.CheckConstraint("is_enabled OR type != {type}".format(type=RegistrationFormItemType.section_pd),
                           name='pd_section_enabled'),
        db.CheckConstraint("is_enabled OR type != {type} OR personal_data_type NOT IN "
                           "({pt.email}, {pt.first_name}, {pt.last_name})"
                           .format(type=RegistrationFormItemType.field_pd, pt=PersonalDataType),
                           name='pd_field_enabled'),
        db.CheckConstraint("is_required OR type != {type} OR personal_data_type NOT IN "
                           "({pt.email}, {pt.first_name}, {pt.last_name})"
                           .format(type=RegistrationFormItemType.field_pd, pt=PersonalDataType),
                           name='pd_field_required'),
        db.Index('ix_uq_form_items_pd_section', 'registration_form_id', unique=True,
                 postgresql_where=db.text('type = {type}'.format(type=RegistrationFormItemType.section_pd))),
        db.Index('ix_uq_form_items_pd_field', 'registration_form_id', 'personal_data_type', unique=True,
                 postgresql_where=db.text('type = {type}'.format(type=RegistrationFormItemType.field_pd))),
        {'schema': 'event_registration'}
    )
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
    #: The type of a personal data field
    personal_data_type = db.Column(
        PyIntEnum(PersonalDataType),
        nullable=True
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
        nullable=False,
        default=''
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
    #: if the section is only accessible to managers
    is_manager_only = db.Column(
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
            cascade='all, delete-orphan',
            order_by=position
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
        return dict(id=self.id, description=self.description)

    @hybrid_property
    def is_section(self):
        return self.type in {RegistrationFormItemType.section, RegistrationFormItemType.section_pd}

    @is_section.expression
    def is_section(cls):
        return cls.type.in_([RegistrationFormItemType.section, RegistrationFormItemType.section_pd])

    @hybrid_property
    def is_field(self):
        return self.type in {RegistrationFormItemType.field, RegistrationFormItemType.field_pd}

    @is_field.expression
    def is_field(cls):
        return cls.type.in_([RegistrationFormItemType.field, RegistrationFormItemType.field_pd])

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'registration_form_id', is_enabled=True, is_deleted=False, is_manager_only=False,
                           _text=self.title)


class RegistrationFormSection(RegistrationFormItem):
    __mapper_args__ = {
        'polymorphic_identity': RegistrationFormItemType.section
    }

    @property
    def locator(self):
        return dict(self.registration_form.locator, section_id=self.id)

    @property
    def view_data(self):
        field_data = dict(super(RegistrationFormSection, self).view_data,
                          enabled=self.is_enabled,
                          title=self.title,
                          is_manager_only=self.is_manager_only,
                          is_personal_data=False,
                          items=[child.view_data for child in self.children if not child.is_deleted])
        return camelize_keys(field_data)


class RegistrationFormPersonalDataSection(RegistrationFormSection):
    __mapper_args__ = {
        'polymorphic_identity': RegistrationFormItemType.section_pd
    }

    @property
    def view_data(self):
        field_data = dict(super(RegistrationFormPersonalDataSection, self).view_data, is_personal_data=True)
        del field_data['isPersonalData']
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
        field_data = dict(super(RegistrationFormText, self).view_data, is_enabled=self.is_enabled,
                          input_type='label', title=self.title, **self.current_data.versioned_data)
        return camelize_keys(field_data)
