# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.dialects.postgresql import JSONB

from indico.core.db import db
from indico.core.db.sqlalchemy.custom.unaccent import define_unaccented_lowercase_index
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
    # - user_affiliations (UserAffiliation.affiliation_link)

    def __repr__(self):
        return format_repr(self, 'id', _text=self.name)


class UserAffiliation(db.Model):
    __tablename__ = 'affiliations'
    __table_args__ = {'schema': 'users'}

    #: the unique id of the affiliations
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: the id of the associated user
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        index=True
    )
    #: the id of the underlying predefined affiliation
    affiliation_id = db.Column(
        db.ForeignKey('indico.affiliations.id'),
        nullable=True,
        index=True
    )
    #: the affiliation
    name = db.Column(
        db.String,
        nullable=False,
        index=True
    )

    #: the predefined affiliation
    affiliation_link = db.relationship(
        'Affiliation',
        lazy=False,
        backref=db.backref('user_affiliations', lazy='dynamic')
    )

    # relationship backrefs:
    # - user (User._affiliation)

    def __repr__(self):
        return format_repr(self, 'id', 'affiliation_id', _text=self.name)


define_unaccented_lowercase_index(UserAffiliation.name)
