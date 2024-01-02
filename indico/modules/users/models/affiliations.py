# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.dialects.postgresql import JSONB

from indico.core.db import db
from indico.util.string import format_repr


class Affiliation(db.Model):
    __tablename__ = 'affiliations'
    __table_args__ = (db.Index(None, 'meta', postgresql_using='gin'),
                      {'schema': 'indico'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False,
        index=True
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )
    street = db.Column(
        db.String,
        nullable=False,
        default='',
    )
    postcode = db.Column(
        db.String,
        nullable=False,
        default='',
    )
    city = db.Column(
        db.String,
        nullable=False,
        default='',
    )
    country_code = db.Column(
        db.String,
        nullable=False,
        default='',
    )
    #: Opaque external data related to this affiliation
    meta = db.Column(
        JSONB,
        nullable=False,
        default={},
    )

    # relationship backrefs:
    # - abstract_links (AbstractPersonLink._affiliation_link)
    # - contribution_links (ContributionPersonLink._affiliation_link)
    # - event_links (EventPersonLink._affiliation_link)
    # - event_person_affiliations (EventPerson.affiliation_link)
    # - session_block_links (SessionBlockPersonLink._affiliation_link)
    # - subcontribution_links (SubContributionPersonLink._affiliation_link)
    # - user_affiliations (User.affiliation_link)

    def __repr__(self):
        return format_repr(self, 'id', _text=self.name)

    @classmethod
    def get_or_create_from_data(cls, affiliation_data):
        existing = cls.query.filter_by(name=affiliation_data['name'], city=affiliation_data['city'],
                                       country_code=affiliation_data['country_code']).order_by(Affiliation.id).first()
        if existing:
            return existing
        return cls(**affiliation_data)
