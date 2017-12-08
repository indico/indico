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

from indico.core.db.sqlalchemy import PyIntEnum, db
from indico.core.db.sqlalchemy.review_questions import ReviewQuestionMixin
from indico.modules.events.papers.models.reviews import PaperReviewType
from indico.modules.events.reviewing_questions_fields import get_reviewing_field_types
from indico.util.locators import locator_property


class PaperReviewQuestion(ReviewQuestionMixin, db.Model):
    __tablename__ = 'review_questions'
    __table_args__ = {'schema': 'event_paper_reviewing'}

    event_backref_name = 'paper_review_questions'

    type = db.Column(
        PyIntEnum(PaperReviewType),
        nullable=False
    )

    # relationship backrefs:
    # - ratings (PaperReviewRating.question)

    @locator_property
    def locator(self):
        return dict(self.event.locator, question_id=self.id, review_type=self.type.name)

    @property
    def field(self):
        try:
            impl = get_reviewing_field_types('papers')[self.field_type]
        except KeyError:
            return None
        return impl(self)
