# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


class ReviewRatingMixin(object):
    question_class = None
    review_class = None

    @declared_attr
    def id(cls):
        return db.Column(
            db.Integer,
            primary_key=True
        )

    @declared_attr
    def question_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('{}.id'.format(cls.question_class.__table__.fullname)),
            index=True,
            nullable=False
        )

    @declared_attr
    def review_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('{}.id'.format(cls.review_class.__table__.fullname)),
            index=True,
            nullable=False
        )

    @declared_attr
    def value(cls):
        return db.Column(
            JSONB,
            nullable=False
        )

    @declared_attr
    def question(cls):
        return db.relationship(
            cls.question_class,
            lazy=True,
            backref=db.backref(
                'ratings',
                cascade='all, delete-orphan',
                lazy=True
            )
        )

    @declared_attr
    def review(cls):
        return db.relationship(
            cls.review_class,
            lazy=True,
            backref=db.backref(
                'ratings',
                cascade='all, delete-orphan',
                lazy=True
            )
        )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'review_id', 'question_id')
