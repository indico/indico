# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from itertools import chain
from operator import attrgetter

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.descriptions import RenderMode, RenderModeMixin
from indico.modules.events.models.reviews import ProposalRevisionMixin
from indico.modules.events.papers.models.reviews import PaperJudgmentProxy, PaperReviewType
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii
from indico.util.struct.enum import RichIntEnum


class PaperRevisionState(RichIntEnum):
    __titles__ = [None, _("Submitted"), _("Accepted"), _("Rejected"), _("To be corrected")]
    __css_classes__ = [None, 'highlight', 'success', 'error', 'warning']
    submitted = 1
    accepted = 2
    rejected = 3
    to_be_corrected = 4


class PaperRevision(ProposalRevisionMixin, RenderModeMixin, db.Model):
    __tablename__ = 'revisions'
    __table_args__ = (db.Index(None, 'contribution_id', unique=True,
                               postgresql_where=db.text('state = {}'.format(PaperRevisionState.accepted))),
                      db.UniqueConstraint('contribution_id', 'submitted_dt'),
                      db.CheckConstraint('(state IN ({}, {}, {})) = (judge_id IS NOT NULL)'
                                         .format(PaperRevisionState.accepted, PaperRevisionState.rejected,
                                                 PaperRevisionState.to_be_corrected),
                                         name='judge_if_judged'),
                      db.CheckConstraint('(state IN ({}, {}, {})) = (judgment_dt IS NOT NULL)'
                                         .format(PaperRevisionState.accepted, PaperRevisionState.rejected,
                                                 PaperRevisionState.to_be_corrected),
                                         name='judgment_dt_if_judged'),
                      {'schema': 'event_paper_reviewing'})

    possible_render_modes = {RenderMode.markdown}
    default_render_mode = RenderMode.markdown
    proposal_attr = 'paper'

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    state = db.Column(
        PyIntEnum(PaperRevisionState),
        nullable=False,
        default=PaperRevisionState.submitted
    )
    _contribution_id = db.Column(
        'contribution_id',
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        index=True,
        nullable=False
    )
    submitter_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    submitted_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    judge_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True
    )
    judgment_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    _judgment_comment = db.Column(
        'judgment_comment',
        db.Text,
        nullable=False,
        default=''
    )

    _contribution = db.relationship(
        'Contribution',
        lazy=True,
        backref=db.backref(
            '_paper_revisions',
            lazy=True,
            order_by=submitted_dt.asc()
        )
    )
    submitter = db.relationship(
        'User',
        lazy=True,
        foreign_keys=submitter_id,
        backref=db.backref(
            'paper_revisions',
            lazy='dynamic'
        )
    )
    judge = db.relationship(
        'User',
        lazy=True,
        foreign_keys=judge_id,
        backref=db.backref(
            'judged_papers',
            lazy='dynamic'
        )
    )

    judgment_comment = RenderModeMixin.create_hybrid_property('_judgment_comment')

    # relationship backrefs:
    # - comments (PaperReviewComment.paper_revision)
    # - files (PaperFile.paper_revision)
    # - reviews (PaperReview.revision)

    def __init__(self, *args, **kwargs):
        paper = kwargs.pop('paper', None)
        if paper:
            kwargs.setdefault('_contribution', paper.contribution)
        super(PaperRevision, self).__init__(*args, **kwargs)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', '_contribution_id', state=None)

    @locator_property
    def locator(self):
        return dict(self.paper.locator, revision_id=self.id)

    @property
    def paper(self):
        return self._contribution.paper

    @property
    def is_last_revision(self):
        return self == self.paper.last_revision

    @property
    def number(self):
        return self.paper.revisions.index(self) + 1

    @property
    def spotlight_file(self):
        return self.get_spotlight_file()

    @property
    def timeline(self):
        return self.get_timeline()

    @paper.setter
    def paper(self, paper):
        self._contribution = paper.contribution

    def get_timeline(self, user=None):
        comments = [x for x in self.comments if x.can_view(user)] if user else self.comments
        reviews = [x for x in self.reviews if x.can_view(user)] if user else self.reviews
        judgment = [PaperJudgmentProxy(self)] if self.state == PaperRevisionState.to_be_corrected else []
        return sorted(chain(comments, reviews, judgment), key=attrgetter('created_dt'))

    def get_reviews(self, group=None, user=None):
        reviews = []
        if user and group:
            reviews = [x for x in self.reviews if x.group.instance == group and x.user == user]
        elif user:
            reviews = [x for x in self.reviews if x.user == user]
        elif group:
            reviews = [x for x in self.reviews if x.group.instance == group]
        return reviews

    def get_reviewed_for_groups(self, user, include_reviewed=False):
        from indico.modules.events.papers.models.reviews import PaperTypeProxy
        from indico.modules.events.papers.util import is_type_reviewing_possible

        cfp = self.paper.cfp
        reviewed_for = set()
        if include_reviewed:
            reviewed_for = {x.type for x in self.reviews if x.user == user and is_type_reviewing_possible(cfp, x.type)}
        if is_type_reviewing_possible(cfp, PaperReviewType.content) and user in self.paper.cfp.content_reviewers:
            reviewed_for.add(PaperReviewType.content)
        if is_type_reviewing_possible(cfp, PaperReviewType.layout) and user in self.paper.cfp.layout_reviewers:
            reviewed_for.add(PaperReviewType.layout)
        return set(map(PaperTypeProxy, reviewed_for))

    def has_user_reviewed(self, user, review_type=None):
        from indico.modules.events.papers.models.reviews import PaperReviewType
        if review_type:
            if isinstance(review_type, basestring):
                review_type = PaperReviewType[review_type]
            return any(review.user == user and review.type == review_type for review in self.reviews)
        else:
            layout_review = next((review for review in self.reviews
                                  if review.user == user and review.type == PaperReviewType.layout), None)
            content_review = next((review for review in self.reviews
                                   if review.user == user and review.type == PaperReviewType.content), None)
            if user in self._contribution.paper_layout_reviewers and user in self._contribution.paper_content_reviewers:
                return bool(layout_review and content_review)
            elif user in self._contribution.paper_layout_reviewers:
                return bool(layout_review)
            elif user in self._contribution.paper_content_reviewers:
                return bool(content_review)

    def get_spotlight_file(self):
        pdf_files = [paper_file for paper_file in self.files if paper_file.content_type == 'application/pdf']
        return pdf_files[0] if len(pdf_files) == 1 else None
