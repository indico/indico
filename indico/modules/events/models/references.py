# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.util.locators import locator_property
from indico.util.string import format_repr


class ReferenceType(db.Model):
    __tablename__ = 'reference_types'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_reference_types_name_lower', db.func.lower(cls.name), unique=True),
                {'schema': 'indico'})

    #: The unique ID of the reference type
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The name of the referenced system
    name = db.Column(
        db.String,
        nullable=False
    )
    #: The scheme used to build an URN for the reference
    scheme = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    #: A URL template to build a link to a referenced entity
    url_template = db.Column(
        db.String,
        nullable=False,
        default=''
    )

    # relationship backrefs:
    # - contribution_references (ContributionReference.reference_type)
    # - event_references (EventReference.reference_type)
    # - subcontribution_references (SubContributionReference.reference_type)

    @locator_property
    def locator(self):
        return {'reference_type_id': self.id}

    def __repr__(self):
        return format_repr(self, 'id', 'url_template', _text=self.name)


class ReferenceModelBase(db.Model):
    __abstract__ = True
    #: The name of the backref on the `ReferenceType`
    reference_backref_name = None

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    value = db.Column(
        db.String,
        nullable=False
    )

    @declared_attr
    def reference_type_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('indico.reference_types.id'),
            nullable=False,
            index=True
        )

    @declared_attr
    def reference_type(cls):
        return db.relationship(
            'ReferenceType',
            lazy=False,
            backref=db.backref(
                cls.reference_backref_name,
                cascade='all, delete-orphan',
                lazy=True
            )
        )

    @property
    def url(self):
        """The URL of the referenced entity.

        ``None`` if no URL template is defined.
        """
        template = self.reference_type.url_template
        if not template:
            return None
        # XXX: Should the value be urlencoded?
        return template.replace('{value}', self.value)

    @property
    def urn(self):
        """The URN of the referenced entity.

        ``None`` if no scheme is defined.
        """
        scheme = self.reference_type.scheme
        if not scheme:
            return None
        return f'{scheme}:{self.value}'


class EventReference(ReferenceModelBase):
    __tablename__ = 'event_references'
    __table_args__ = {'schema': 'events'}
    reference_backref_name = 'event_references'

    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - event (Event.references)

    def __repr__(self):
        return format_repr(self, 'id', 'event_id', 'reference_type_id', _text=self.value)
