# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.review_comments import ReviewCommentMixin
from indico.modules.events.models.reviews import ProposalCommentMixin
from indico.modules.events.papers.models.reviews import PaperCommentVisibility
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii, text_to_repr


class PaperReviewComment(ProposalCommentMixin, ReviewCommentMixin, db.Model):
    __tablename__ = 'review_comments'
    __table_args__ = {'schema': 'event_paper_reviewing'}
    user_backref_name = 'review_comments'
    user_modified_backref_name = 'modified_review_comments'

    @declared_attr
    def revision_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('event_paper_reviewing.revisions.id'),
            index=True,
            nullable=False
        )

    @declared_attr
    def visibility(cls):
        return db.Column(
            PyIntEnum(PaperCommentVisibility),
            nullable=False,
            default=PaperCommentVisibility.contributors
        )

    @declared_attr
    def paper_revision(cls):
        return db.relationship(
            'PaperRevision',
            lazy=True,
            backref=db.backref(
                'comments',
                primaryjoin='(PaperReviewComment.revision_id == PaperRevision.id) & ~PaperReviewComment.is_deleted',
                order_by=cls.created_dt,
                cascade='all, delete-orphan',
                lazy=True,
            )
        )

    @locator_property
    def locator(self):
        return dict(self.paper_revision.locator, comment_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'revision_id', is_deleted=False, _text=text_to_repr(self.text))

    def can_edit(self, user):
        if user is None:
            return False
        elif self.user == user:
            return True
        elif self.paper_revision.paper.event.cfp.is_manager(user):
            return True
        else:
            return False

    def can_view(self, user):
        if user is None:
            return False
        elif user == self.user:
            return True
        elif self.visibility == PaperCommentVisibility.users:
            return True
        paper = self.paper_revision.paper
        visibility_checks = {PaperCommentVisibility.judges: [paper.can_judge],
                             PaperCommentVisibility.reviewers: [paper.can_judge,
                                                                paper.can_review],
                             PaperCommentVisibility.contributors: [paper.can_judge,
                                                                   paper.can_review,
                                                                   paper.can_submit]}
        return any(fn(user) for fn in visibility_checks[self.visibility])
