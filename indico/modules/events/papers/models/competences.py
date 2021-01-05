# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy import ARRAY

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


class PaperCompetence(db.Model):
    __tablename__ = 'competences'
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id'),
                      {'schema': 'event_paper_reviewing'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    competences = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'paper_competences',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'paper_competences',
            lazy='dynamic'
        )
    )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'user_id', 'event_id', _text=', '.join(self.competences))

    @classmethod
    def merge_users(cls, target, source):
        source_competences = source.paper_competences.all()
        target_competences_by_event = {x.event: x for x in target.paper_competences}
        for comp in source_competences:
            existing = target_competences_by_event.get(comp.event)
            if existing is None:
                comp.user_id = target.id
            else:
                existing.competences = list(set(existing.competences) | set(comp.competences))
                db.session.delete(comp)
