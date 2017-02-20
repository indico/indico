# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from itertools import chain
from operator import attrgetter

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime, PyIntEnum
from indico.core.db.sqlalchemy.descriptions import RenderModeMixin, RenderMode
from indico.modules.events.models.reviews import ProposalRevisionMixin
from indico.modules.events.papers.models.reviews import PaperReviewType
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import return_ascii, format_repr
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

    @paper.setter
    def paper(self, paper):
        self._contribution = paper.contribution

    def get_timeline(self, user=None):
        comments = [x for x in self.comments if x.can_view(user)] if user else self.comments
        reviews = [x for x in self.reviews if x.can_view(user)] if user else self.reviews
        return sorted(chain(comments, reviews), key=attrgetter('created_dt'))

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
        reviewed_for = {x.type for x in self.reviews if x.user == user} if include_reviewed else set()
        if self.paper.cfp.content_reviewing_enabled and user in self.paper.cfp.content_reviewers:
            reviewed_for.add(PaperReviewType.content)
        if self.paper.cfp.layout_reviewing_enabled and user in self.paper.cfp.layout_reviewers:
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
