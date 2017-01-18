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


from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime, PyIntEnum
from indico.core.db.sqlalchemy.descriptions import RenderModeMixin, RenderMode
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import return_ascii, format_repr
from indico.util.struct.enum import RichIntEnum


class PaperRevisionState(RichIntEnum):
    __titles__ = [None, _("Submitted"), _("Accepted"), _("Rejected"), _("To be corrected")]
    submitted = 1
    accepted = 2
    rejected = 3
    to_be_corrected = 4


class PaperRevision(RenderModeMixin, db.Model):
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
            order_by=submitted_dt.desc()
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

    @paper.setter
    def paper(self, paper):
        self._contribution = paper.contribution
