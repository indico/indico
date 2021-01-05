# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db
from indico.util.string import format_repr


class EventSeries(db.Model):
    """A series of events."""

    __tablename__ = 'series'
    __table_args__ = {'schema': 'events'}

    #: The ID of the series
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: Whether to show the sequence number of an event in its title
    #: on category display pages and on the main event page.
    show_sequence_in_title = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: Whether to show links to the other events in the same series
    #: on the main event page.
    show_links = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # relationship backrefs:
    # - events (Event.series)

    def __repr__(self):
        return format_repr(self, 'id')
