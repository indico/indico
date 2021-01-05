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


class EventLabel(db.Model):
    __tablename__ = 'labels'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_labels_title_lower', db.func.lower(cls.title), unique=True),
                {'schema': 'events'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    color = db.Column(
        db.String,
        nullable=False
    )

    # relationship backrefs:
    # - events (Event.label)

    @locator_property
    def locator(self):
        return {'event_label_id': self.id}

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.title)
