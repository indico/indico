# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


class ContributionType(db.Model):
    __tablename__ = 'contribution_types'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_contribution_types_event_id_name_lower', cls.event_id, db.func.lower(cls.name),
                         unique=True),
                {'schema': 'events'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    name = db.Column(
        db.String,
        nullable=False
    )
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    is_private = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'contribution_types',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - abstract_reviews (AbstractReview.proposed_contribution_type)
    # - abstracts_accepted (Abstract.accepted_contrib_type)
    # - contributions (Contribution.type)
    # - proposed_abstracts (Abstract.submitted_contrib_type)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.name)

    @locator_property
    def locator(self):
        return dict(self.event.locator, contrib_type_id=self.id)
