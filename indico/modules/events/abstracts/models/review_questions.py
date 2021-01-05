# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.review_questions import ReviewQuestionMixin
from indico.modules.events.reviewing_questions_fields import get_reviewing_field_types
from indico.util.locators import locator_property


class AbstractReviewQuestion(ReviewQuestionMixin, db.Model):
    __tablename__ = 'abstract_review_questions'
    __table_args__ = {'schema': 'event_abstracts'}

    event_backref_name = 'abstract_review_questions'

    # relationship backrefs:
    # - ratings (AbstractReviewRating.question)

    @locator_property
    def locator(self):
        return dict(self.event.locator, question_id=self.id)

    @property
    def field(self):
        try:
            impl = get_reviewing_field_types('abstracts')[self.field_type]
        except KeyError:
            return None
        return impl(self)
