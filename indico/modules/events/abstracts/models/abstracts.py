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

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin, RenderMode
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.modules.events.abstracts.models.reviews import AbstractAction
from indico.modules.events.contributions.models.contributions import _get_next_friendly_id, CustomFieldsMixin
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii, text_to_repr
from indico.util.struct.enum import TitledIntEnum


class AbstractState(TitledIntEnum):
    __titles__ = [None, _("Submitted"), _("Withdrawn"), _("Accepted"), _("Rejected"), _("Merged"), _("Duplicate")]
    submitted = 1
    withdrawn = 2
    accepted = 3
    rejected = 4
    merged = 5
    duplicate = 6


class AbstractPublicState(TitledIntEnum):
    __titles__ = [None, _("Awaiting Review"), _("Under Review")]
    awaiting = 1
    under_review = 2


class AbstractReviewingState(TitledIntEnum):
    __titles__ = [_("Not Started"), _("Positive"), _("Negative"), _("Mixed")]
    not_started = 0
    positive = 1
    negative = 2
    mixed = 3


class Abstract(DescriptionMixin, CustomFieldsMixin, db.Model):
    """Represents an abstract that can be associated to a Contribution."""

    __tablename__ = 'abstracts'
    __auto_table_args = (db.UniqueConstraint('friendly_id', 'event_id'),
                         {'schema': 'event_abstracts'})

    possible_render_modes = {RenderMode.markdown}
    default_render_mode = RenderMode.markdown

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The friendly ID for the abstract (same as the legacy id in ZODB)
    friendly_id = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_friendly_id
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    #: ID of the user who submitted the abstract
    submitter_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    submitted_contrib_type_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contribution_types.id'),
        nullable=True,
        index=True
    )
    submitted_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    modified_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=True,
        index=True
    )
    modified_dt = db.Column(
        UTCDateTime,
        nullable=True,
    )
    state = db.Column(
        PyIntEnum(AbstractState),
        nullable=False,
        default=AbstractState.submitted
    )
    #: ID of the user who judged the abstract
    judge_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True
    )
    judgment_comment = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    judgment_dt = db.Column(
        UTCDateTime,
        nullable=True,
    )
    accepted_track_id = db.Column(
        db.Integer,
        db.ForeignKey('events.tracks.id'),
        nullable=True,
        index=True
    )
    accepted_contrib_type_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contribution_types.id'),
        nullable=True,
        index=True
    )
    merged_into_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        index=True,
        nullable=True
    )
    duplicate_of_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        index=True,
        nullable=True
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
            'abstracts',
            primaryjoin='(Abstract.event_id == Event.id) & ~Abstract.is_deleted',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    #: User who submitted the abstract
    submitter = db.relationship(
        'User',
        lazy=True,
        foreign_keys=submitter_id,
        backref=db.backref(
            'abstracts',
            primaryjoin='(Abstract.submitter_id == User.id) & ~Abstract.is_deleted',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    modified_by = db.relationship(
        'User',
        lazy=True,
        foreign_keys=modified_by_id,
        backref=db.backref(
            'modified_abstracts',
            primaryjoin='(Abstract.modified_by_id == User.id) & ~Abstract.is_deleted',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    submitted_contrib_type = db.relationship(
        'ContributionType',
        lazy=True,
        foreign_keys=submitted_contrib_type_id,
        backref=db.backref(
            'proposed_abstracts',
            primaryjoin='(Abstract.submitted_contrib_type_id == ContributionType.id) & ~Abstract.is_deleted',
            lazy=True
        )
    )
    submitted_for_tracks = db.relationship(
        'Track',
        secondary='event_abstracts.submitted_for_tracks',
        collection_class=set,
        backref=db.backref(
            'abstracts_submitted',
            primaryjoin='event_abstracts.submitted_for_tracks.c.track_id == Track.id',
            secondaryjoin='(event_abstracts.submitted_for_tracks.c.abstract_id == Abstract.id) & ~Abstract.is_deleted',
            collection_class=set,
            lazy=True
        )
    )
    proposed_for_tracks = db.relationship(
        'Track',
        secondary='event_abstracts.proposed_for_tracks',
        collection_class=set,
        backref=db.backref(
            'abstracts_proposed',
            primaryjoin='event_abstracts.proposed_for_tracks.c.track_id == Track.id',
            secondaryjoin='(event_abstracts.proposed_for_tracks.c.abstract_id == Abstract.id) & ~Abstract.is_deleted',
            collection_class=set,
            lazy=True
        )
    )
    #: User who judged the abstract
    judge = db.relationship(
        'User',
        lazy=True,
        foreign_keys=judge_id,
        backref=db.backref(
            'judged_abstracts',
            primaryjoin='(Abstract.judge_id == User.id) & ~Abstract.is_deleted',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    accepted_track = db.relationship(
        'Track',
        lazy=True,
        backref=db.backref(
            'abstracts_accepted',
            primaryjoin='(Abstract.accepted_track_id == Track.id) & ~Abstract.is_deleted',
            lazy=True
        )
    )
    accepted_contrib_type = db.relationship(
        'ContributionType',
        lazy=True,
        foreign_keys=accepted_contrib_type_id,
        backref=db.backref(
            'abstracts_accepted',
            primaryjoin='(Abstract.accepted_contrib_type_id == ContributionType.id) & ~Abstract.is_deleted',
            lazy=True
        )
    )
    merged_into = db.relationship(
        'Abstract',
        lazy=True,
        remote_side=id,
        foreign_keys=merged_into_id,
        backref=db.backref(
            'merged_abstracts',
            primaryjoin=(db.remote(merged_into_id) == id) & ~db.remote(is_deleted),
            lazy=True
        )
    )
    duplicate_of = db.relationship(
        'Abstract',
        lazy=True,
        remote_side=id,
        foreign_keys=duplicate_of_id,
        backref=db.backref(
            'duplicate_abstracts',
            primaryjoin=(db.remote(duplicate_of_id) == id) & ~db.remote(is_deleted),
            lazy=True
        )
    )
    #: Data stored in abstract/contribution fields
    field_values = db.relationship(
        'AbstractFieldValue',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'abstract',
            lazy=True
        )
    )

    # relationship backrefs:
    # - comments (AbstractComment.abstract)
    # - contribution (Contribution.abstract)
    # - duplicate_abstracts (Abstract.duplicate_of)
    # - email_logs (AbstractEmailLogEntry.abstract)
    # - merged_abstracts (Abstract.merged_into)
    # - reviews (AbstractReview.abstract)

    @property
    def public_state(self):
        if self.state != AbstractState.submitted:
            return self.state
        elif self.reviews:
            return AbstractPublicState.under_review
        else:
            return AbstractPublicState.awaiting

    @property
    def reviewing_state(self):
        if not self.reviews:
            return AbstractReviewingState.not_started
        rejections = any(x.action == AbstractAction.reject for x in self.reviews)
        acceptances = any(x.action == AbstractAction.accept for x in self.reviews)
        if acceptances and not rejections:
            return AbstractReviewingState.positive
        elif rejections and not acceptances:
            return AbstractReviewingState.negative
        else:
            return AbstractReviewingState.mixed

    @locator_property
    def locator(self):
        return dict(self.event_new.locator, abstract_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'event_id', is_deleted=False, _text=text_to_repr(self.title))
