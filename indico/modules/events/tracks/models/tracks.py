# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin, RenderMode
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii, text_to_repr


def _get_next_position(context):
    event_id = context.current_parameters['event_id']
    res = db.session.query(db.func.max(Track.position)).filter_by(event_id=event_id).one()
    return (res[0] or 0) + 1


class Track(DescriptionMixin, db.Model):
    __tablename__ = 'tracks'
    __table_args__ = {'schema': 'events'}

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
    code = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    position = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_position
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'tracks',
            cascade='all, delete-orphan',
            lazy=True,
            order_by=position
        )
    )
    abstract_reviewers = db.relationship(
        'User',
        secondary='events.track_abstract_reviewers',
        collection_class=set,
        lazy=True,
        backref=db.backref(
            'abstract_reviewer_for_tracks',
            collection_class=set,
            lazy=True
        )
    )
    conveners = db.relationship(
        'User',
        secondary='events.track_conveners',
        collection_class=set,
        lazy=True,
        backref=db.backref(
            'convener_for_tracks',
            collection_class=set,
            lazy=True
        )
    )

    # relationship backrefs:
    # - abstract_reviews (AbstractReview.track)
    # - abstracts_accepted (Abstract.accepted_track)
    # - abstracts_reviewed (Abstract.reviewed_for_tracks)
    # - abstracts_submitted (Abstract.submitted_for_tracks)
    # - contributions (Contribution.track)
    # - proposed_abstract_reviews (AbstractReview.proposed_tracks)

    @property
    def short_title(self):
        return self.code if self.code else self.title

    @property
    def full_title(self):
        return '{} - {}'.format(self.code, self.title) if self.code else self.title

    @locator_property
    def locator(self):
        return dict(self.event.locator, track_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=text_to_repr(self.title))

    def can_delete(self, user):
        return self.event.can_manage(user) and not self.abstracts_accepted

    def can_review_abstracts(self, user):
        if not user:
            return False
        elif not self.event.can_manage(user, role='abstract_reviewer', explicit_role=True):
            return False
        elif user in self.event.global_abstract_reviewers:
            return True
        elif user in self.abstract_reviewers:
            return True
        else:
            return False

    def can_convene(self, user):
        if not user:
            return False
        elif not self.event.can_manage(user, role='track_convener', explicit_role=True):
            return False
        elif user in self.event.global_conveners:
            return True
        elif user in self.conveners:
            return True
        else:
            return False
