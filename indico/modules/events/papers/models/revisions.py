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

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime, PyIntEnum
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import return_ascii, format_repr
from indico.util.struct.enum import TitledIntEnum


class PaperRevisionState(TitledIntEnum):
    __titles__ = [None, _("Submitted"), _("Accepted"), _("Rejected"), _("To be corrected")]
    submitted = 1
    accepted = 2
    rejected = 3
    to_be_corrected = 4


class PaperRevision(db.Model):
    __tablename__ = 'revisions'
    __table_args__ = (db.Index(None, 'contribution_id', unique=True,
                               postgresql_where=db.text('state = {}'.format(PaperRevisionState.accepted))),
                      {'schema': 'event_paper_reviewing'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    contribution_id = db.Column(
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
    state = db.Column(
        PyIntEnum(PaperRevisionState),
        nullable=False,
        default=PaperRevisionState.submitted
    )

    contribution = db.relationship(
        'Contribution',
        lazy=True,
        backref=db.backref(
            'paper_revisions',
            lazy=True,
            order_by=submitted_dt.desc()
        )
    )
    submitter = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'paper_revisions',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - comments (PaperReviewComment.paper_revision)
    # - files (PaperFile.paper_revision)
    # - reviews (PaperReview.revision)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'contribution_id', state=None)

    @locator_property
    def locator(self):
        return dict(self.contribution.locator, revision_id=self.id)
