# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin, RenderMode
from indico.modules.events.tracks.models.tracks import get_next_position
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii, text_to_repr


class TrackGroup(DescriptionMixin, db.Model):
    __tablename__ = 'track_groups'
    __table_args__ = {'schema': 'events'}

    is_track_group = True

    possible_render_modes = {RenderMode.markdown}
    default_render_mode = RenderMode.markdown

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    position = db.Column(
        db.Integer,
        nullable=False,
        default=get_next_position
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'track_groups',
            cascade='all, delete-orphan',
            lazy=True,
            order_by=id
        )
    )

    # relationship backrefs:
    # - tracks (Track.track_group)

    @locator_property
    def locator(self):
        return dict(self.event.locator, track_group_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=text_to_repr(self.title))
