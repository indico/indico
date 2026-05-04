# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db


class EventRating(db.Model):
    __tablename__ = 'event_ratings'
    __table_args__ = {'schema': 'events'}

    event_id = db.Column(db.Integer, db.ForeignKey('events.events.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.users.id'), primary_key=True)
    rating = db.Column(db.Integer, nullable=False)

    event = db.relationship('Event', backref=db.backref('ratings', lazy='dynamic'))
