# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db


class LegacyEventMapping(db.Model):
    """Legacy event ID mapping.

    Legacy events (imported from CDS agenda) have non-numeric IDs
    which are not supported by any new code. This mapping maps them
    to proper integer IDs to avoid breaking things.
    """

    __tablename__ = 'legacy_id_map'
    __table_args__ = {'schema': 'events'}

    legacy_event_id = db.Column(
        db.String,
        primary_key=True,
        index=True
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        primary_key=True,
        autoincrement=False
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'legacy_mapping',
            uselist=False,
            lazy=True
        )
    )

    def __repr__(self):
        return f'<LegacyEventMapping({self.legacy_event_id}, {self.event_id})>'
