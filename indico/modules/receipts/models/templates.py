# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import yaml
from sqlalchemy.ext.hybrid import Comparator, hybrid_property

from indico.core.db import db
from indico.modules.logs.models.entries import CategoryLogRealm, EventLogRealm
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
        nullable=False,
        default='',
    )
    yaml = db.Column(
        db.String,
        nullable=False,
        default='',
    )
    default_filename = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    category = db.relationship(
        'Category',
        lazy=True,
        foreign_keys=category_id,
        backref=db.backref(
            'receipt_templates',
            primaryjoin='(ReceiptTemplate.category_id == Category.id) & ~ReceiptTemplate.is_deleted',
            lazy=True
        )
    )
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'receipt_templates',
            primaryjoin='(ReceiptTemplate.event_id == Event.id) & ~ReceiptTemplate.is_deleted',
            lazy=True
        )
    )

    # relationship backrefs:
    # - receipt_files (ReceiptFile.template)

    @hybrid_property
    def owner(self):
        return self.event or self.category

    @owner.comparator
    def owner(cls):
        return _OwnerComparator(cls)

    @property
    def custom_fields(self):
        data = yaml.safe_load(self.yaml) or {}
        return data.get('custom_fields', [])

    @locator_property
    def locator(self):
        return dict(self.owner.locator, template_id=self.id)

    @property
    def log_realm(self):
        return EventLogRealm.management if self.event else CategoryLogRealm.category

    def log(self, *args, **kwargs):
        """Log with prefilled metadata for the receipt template."""
        return self.owner.log(*args, meta={'receipt_template_id': self.id}, **kwargs)

    def __repr__(self):
        return format_repr(self, 'id', 'event_id', 'category_id', is_deleted=False, _text=self.title)


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
            raise TypeError(f'Unexpected object type {type(other)}: {other}')
