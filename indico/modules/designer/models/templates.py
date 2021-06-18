# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import Comparator, hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.designer import DEFAULT_CONFIG, TemplateType
from indico.util.locators import locator_property
from indico.util.placeholders import get_placeholders
from indico.util.string import format_repr


TEMPLATE_DEFAULTS = {
    'items': [],
    'background_position': 'stretch'
}


class DesignerTemplate(db.Model):
    __tablename__ = 'designer_templates'
    __table_args__ = (db.CheckConstraint('(event_id IS NULL) != (category_id IS NULL)', 'event_xor_category_id_null'),
                      {'schema': 'indico'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    type = db.Column(
        PyIntEnum(TemplateType),
        nullable=False
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=True
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        index=True,
        nullable=True
    )
    data = db.Column(
        JSONB,
        nullable=False
    )
    background_image_id = db.Column(
        db.Integer,
        db.ForeignKey('indico.designer_image_files.id'),
        index=False,
        nullable=True
    )
    backside_template_id = db.Column(
        db.ForeignKey('indico.designer_templates.id'),
        index=True,
        nullable=True
    )
    is_clonable = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    is_system_template = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    category = db.relationship(
        'Category',
        lazy=True,
        foreign_keys=category_id,
        backref=db.backref(
            'designer_templates',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'designer_templates',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    background_image = db.relationship(
        'DesignerImageFile',
        lazy=True,
        foreign_keys=background_image_id,
        post_update=True
    )
    backside_template = db.relationship(
        'DesignerTemplate',
        lazy=True,
        remote_side=id,
        backref='backside_template_of'
    )

    # relationship backrefs:
    # - backside_template_of (DesignerTemplate.backside_template)
    # - default_badge_template_of (Category.default_badge_template)
    # - default_ticket_template_of (Category.default_ticket_template)
    # - images (DesignerImageFile.template)
    # - ticket_for_regforms (RegistrationForm.ticket_template)

    def __init__(self, **kwargs):
        data = kwargs.pop('data', None)
        tpl_type = kwargs.get('type')
        if data is None:
            data = {
                'items': [],
                'background_position': 'stretch'
            }
            size = DEFAULT_CONFIG[tpl_type]['tpl_size']
            data.update({'width': size[0], 'height': size[1]})
        super().__init__(data=data, **kwargs)

    @hybrid_property
    def owner(self):
        return self.event if self.event else self.category

    @owner.comparator
    def owner(cls):
        return _OwnerComparator(cls)

    @locator_property
    def locator(self):
        return dict(self.owner.locator, template_id=self.id)

    @property
    def is_ticket(self):
        placeholders = get_placeholders('designer-fields')
        if any(placeholders[item['type']].is_ticket for item in self.data['items'] if item['type'] in placeholders):
            return True
        elif self.backside_template and self.backside_template.is_ticket:
            return True
        else:
            return False

    def __repr__(self):
        return format_repr(self, 'id', 'event_id', 'category_id', _text=self.title)


class _OwnerComparator(Comparator):
    def __init__(self, cls):
        self.cls = cls

    def __clause_element__(self):
        # just in case
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, db.m.Event):
            return self.cls.event == other
        elif isinstance(other, db.m.Category):
            return self.cls.category == other
        else:
            raise ValueError(f'Unexpected object type {type(other)}: {other}')
