# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db
from indico.core.db.sqlalchemy.custom.unaccent import define_unaccented_lowercase_index
from indico.util.string import format_repr


class Affiliation(db.Model):
    __tablename__ = 'affiliations'
    __table_args__ = {'schema': 'indico'}

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

    # relationship backrefs:
    # - user_affiliations (UserAffiliation.affiliation)

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
    affiliation = db.relationship(
        'Affiliation',
        lazy=False,
        backref=db.backref('user_affiliations', lazy='dynamic')
    )

    # relationship backrefs:
    # - user (User._affiliation)

    def __repr__(self):
        return format_repr(self, 'id', 'affiliation_id', _text=self.name)


define_unaccented_lowercase_index(UserAffiliation.name)
