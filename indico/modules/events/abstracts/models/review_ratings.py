# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.review_ratings import ReviewRatingMixin
from indico.modules.events.abstracts.models.review_questions import AbstractReviewQuestion
from indico.modules.events.abstracts.models.reviews import AbstractReview


class AbstractReviewRating(ReviewRatingMixin, db.Model):
    __tablename__ = 'abstract_review_ratings'
    __table_args__ = (db.UniqueConstraint('review_id', 'question_id'),
                      {'schema': 'event_abstracts'})

    question_class = AbstractReviewQuestion
    review_class = AbstractReview
