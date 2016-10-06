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

from indico.core.db.sqlalchemy import db
from indico.util.string import format_repr, return_ascii


def _get_next_position(context):
    event_id = context.current_parameters['event_id']
    res = db.session.query(db.func.max(AbstractReviewQuestion.position)).filter_by(event_id=event_id,
                                                                                   is_deleted=False).one()
    return (res[0] or 0) + 1


class AbstractReviewQuestion(db.Model):
    __tablename__ = 'abstract_review_questions'
    __table_args__ = {'schema': 'event_abstracts'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    text = db.Column(
        db.Text,
        nullable=False
    )
    no_score = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    position = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_position
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'abstract_review_questions',
            primaryjoin='(AbstractReviewQuestion.event_id == Event.id) & ~AbstractReviewQuestion.is_deleted',
            order_by=position,
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    # relationship backrefs:
    # - ratings (AbstractReviewRating.question)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'event_id', no_score=False, is_deleted=False, _text=self.text)
