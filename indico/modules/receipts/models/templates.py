# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import Comparator, hybrid_property

from indico.core.db import db
from indico.util.locators import locator_property
from indico.util.string import format_repr


class ReceiptTemplate(db.Model):
    __tablename__ = 'receipt_templates'
    __table_args__ = (db.CheckConstraint('(event_id IS NULL) != (category_id IS NULL)', 'event_xor_category_id_null'),
                      {'schema': 'indico'})

    id = db.Column(
        db.Integer,
        primary_key=True
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
    html = db.Column(
        db.String,
        nullable=False
    )
    css = db.Column(
        db.String,
        nullable=False
    )
    custom_fields = db.Column(
        JSONB,
        nullable=False
    )
    category = db.relationship(
        'Category',
        lazy=True,
        foreign_keys=category_id,
        backref=db.backref(
            'receipt_templates',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'receipt_templates',
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    @hybrid_property
    def owner(self):
        return self.event if self.event else self.category

    @owner.comparator
    def owner(cls):
        return _OwnerComparator(cls)

    @locator_property
    def locator(self):
        return dict(self.owner.locator, template_id=self.id)

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