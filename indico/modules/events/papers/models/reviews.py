# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import division, unicode_literals

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime, db
from indico.core.db.sqlalchemy.descriptions import RenderMode, RenderModeMixin
from indico.modules.events.models.reviews import ProposalGroupProxy, ProposalReviewMixin
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii
from indico.util.struct.enum import RichIntEnum


class PaperAction(RichIntEnum):
    __titles__ = [None, _("Accept"), _("Reject"), _("To be corrected")]
    __css_classes__ = [None, 'success', 'error', 'warning']
    accept = 1
    reject = 2
    to_be_corrected = 3


class PaperReviewType(RichIntEnum):
    __titles__ = [None, _("Layout"), _("Content")]
    layout = 1
    content = 2


class PaperTypeProxy(ProposalGroupProxy):
    @locator_property
    def locator(self):
        return {'review_type': self.instance.name}


class PaperJudgmentProxy(object):
    """A timeline item for the non final judgments."""

    timeline_item_type = 'judgment'

    def __init__(self, paper):
        self.paper = paper

    @property
    def created_dt(self):
        return self.paper.judgment_dt

    @return_ascii
    def __repr__(self):
        return '<PaperJudgmentProxy: {}>'.format(self.paper)


class PaperCommentVisibility(RichIntEnum):
    """Most to least restrictive visibility for paper comments."""
    __titles__ = [None,
                  _("Visible only to judges"),
                  _("Visible to reviewers and judges"),
                  _("Visible to contributors, reviewers, and judges"),
                  _("Visible to all users")]
    judges = 1
    reviewers = 2
    contributors = 3
    users = 4


class PaperReview(ProposalReviewMixin, RenderModeMixin, db.Model):
    """A paper review, emitted by a layout or content reviewer."""

    possible_render_modes = {RenderMode.markdown}
    default_render_mode = RenderMode.markdown

    revision_attr = 'revision'
    group_attr = 'type'
    group_proxy_cls = PaperTypeProxy

    __tablename__ = 'reviews'
    __table_args__ = (db.UniqueConstraint('revision_id', 'user_id', 'type'),
                      {'schema': 'event_paper_reviewing'})
    TIMELINE_TYPE = 'review'

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    revision_id = db.Column(
        db.Integer,
        db.ForeignKey('event_paper_reviewing.revisions.id'),
        index=True,
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc,
    )
    modified_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    _comment = db.Column(
        'comment',
        db.Text,
        nullable=False,
        default=''
    )
    type = db.Column(
        PyIntEnum(PaperReviewType),
        nullable=False
    )
    proposed_action = db.Column(
        PyIntEnum(PaperAction),
        nullable=False
    )

    revision = db.relationship(
        'PaperRevision',
        lazy=True,
        backref=db.backref(
            'reviews',
            lazy=True,
            order_by=created_dt.desc()
        )
    )
    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'paper_reviews',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - ratings (PaperReviewRating.review)

    comment = RenderModeMixin.create_hybrid_property('_comment')

    @locator_property
    def locator(self):
        return dict(self.revision.locator, review_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'type', 'revision_id', 'user_id', proposed_action=None)

    def can_edit(self, user, check_state=False):
        from indico.modules.events.papers.models.revisions import PaperRevisionState
        if user is None:
            return False
        if check_state and self.revision.state != PaperRevisionState.submitted:
            return False
        return self.user == user

    def can_view(self, user):
        if user is None:
            return False
        elif user == self.user:
            return True
        elif self.revision.paper.can_judge(user):
            return True
        return False

    @property
    def visibility(self):
        return PaperCommentVisibility.reviewers

    @property
    def score(self):
        ratings = [r for r in self.ratings
                   if not r.question.is_deleted and r.question.field_type == 'rating' and r.value is not None]
        if not ratings:
            return None
        return sum(x.value for x in ratings) / len(ratings)
