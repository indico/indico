# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.review_ratings import ReviewRatingMixin
from indico.modules.events.papers.models.review_questions import PaperReviewQuestion
from indico.modules.events.papers.models.reviews import PaperReview


class PaperReviewRating(ReviewRatingMixin, db.Model):
    __tablename__ = 'review_ratings'
    __table_args__ = (db.UniqueConstraint('review_id', 'question_id'),
                      {'schema': 'event_paper_reviewing'})

    question_class = PaperReviewQuestion
    review_class = PaperReview
