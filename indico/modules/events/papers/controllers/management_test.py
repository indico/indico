# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.papers.models.papers import Paper
from indico.modules.events.papers.models.review_questions import PaperReviewQuestion
from indico.modules.events.papers.models.review_ratings import PaperReviewRating
from indico.modules.events.papers.models.reviews import PaperAction, PaperReview, PaperReviewType
from indico.modules.events.papers.models.revisions import PaperRevision
from indico.modules.events.papers.settings import paper_reviewing_settings


@pytest.fixture
def dummy_paper(dummy_contribution):
    return Paper(dummy_contribution)


@pytest.mark.parametrize(('value', 'scale_min', 'scale_max', 'expected'), (
    (3, 1, 3, 3),
    (3, 0, 10, 10),
    (-3, 0, 10, 0),
    (0, 0, 10, 5),
    (1, 5, 50, 35),
    (3, 5, 50, 50),
    (None, 0, 10, None)
))
def test_paper_review_scale_ratings(db, dummy_paper, dummy_event, dummy_user,
                                    value, scale_min, scale_max, expected):
    from indico.modules.events.papers.controllers.management import RHManageReviewingSettings
    paper_reviewing_settings.set(dummy_event, 'scale_lower', -3)
    paper_reviewing_settings.set(dummy_event, 'scale_upper', 3)

    question = PaperReviewQuestion(type=PaperReviewType.content, field_type='rating', title='Rating')
    dummy_event.paper_review_questions.append(question)
    revision = PaperRevision(submitter=dummy_user, paper=dummy_paper)
    review = PaperReview(type=PaperReviewType.content, user=dummy_user, proposed_action=PaperAction.accept)
    revision.reviews.append(review)
    rating = PaperReviewRating(question=question, value=value)
    review.ratings.append(rating)
    db.session.flush()

    rh = RHManageReviewingSettings()
    rh.event = dummy_event
    rh._scale_ratings(scale_min, scale_max)
    assert rating.value == expected
