# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from indico.core.db.sqlalchemy import db, UTCDateTime
from indico.util.date_time import now_utc
from indico.util.string import format_repr, return_ascii


class Judgment(db.Model):
    """Represents an abstract judgment, emitted by a judge"""

    __tablename__ = 'judgments'
    __table_args__ = (db.UniqueConstraint('abstract_id', 'track_id', 'judge_user_id'),
                      {'schema': 'event_abstracts'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    creation_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc,
        index=True
    )
    abstract_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        index=True,
        nullable=False
    )
    track_id = db.Column(
        db.Integer,
        nullable=False
    )
    judge_user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        index=True
    )
    accepted_type_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contribution_types.id'),
        nullable=True,
        index=True
    )
    abstract = db.relationship(
        'Abstract',
        lazy=False,
        backref=db.backref(
            'judgments',
            lazy='dynamic'
        )
    )
    judge = db.relationship(
        'User',
        lazy=False,
        backref=db.backref(
            'abstract_judgments',
            lazy='dynamic'
        )
    )
    accepted_type = db.relationship(
        'ContributionType',
        lazy=False,
        backref=db.backref(
            'abstract_judgments',
            lazy='dynamic'
        )
    )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', abstract=self.abstract, judge=self.judge)

    @property
    def as_legacy(self):
        return next((judgment for judgment in self.abstract.as_legacy.getJudgementHistoryByTrack(str(self.track_id))
                    if judgment.getResponsible().as_new == self.judge), None)

    @property
    def track(self):
        return self.event_new.as_legacy.getTrackById(str(self.track_id))
