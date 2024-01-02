# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db
from indico.util.string import format_repr


class LegacyRegistrationMapping(db.Model):
    """Legacy registration id/token mapping.

    Legacy registrations had tokens which are not compatible with the
    new UUID-based ones.
    """

    __tablename__ = 'legacy_registration_map'
    __table_args__ = {'schema': 'event_registration'}

    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        primary_key=True,
        autoincrement=False
    )
    legacy_registrant_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=False
    )
    legacy_registrant_key = db.Column(
        db.String,
        nullable=False
    )
    registration_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.registrations.id'),
        index=True,
        nullable=False
    )

    registration = db.relationship(
        'Registration',
        lazy=False,
        backref=db.backref(
            'legacy_mapping',
            cascade='all, delete-orphan',
            uselist=False,
            lazy=True
        )
    )

    def __repr__(self):
        return format_repr(self, 'event_id', 'legacy_registrant_id', 'legacy_registrant_key', 'registration_id')
