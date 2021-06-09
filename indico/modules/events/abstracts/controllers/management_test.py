# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.review_questions import AbstractReviewQuestion
from indico.modules.events.abstracts.models.review_ratings import AbstractReviewRating
from indico.modules.events.abstracts.models.reviews import AbstractAction, AbstractReview
from indico.modules.events.abstracts.settings import abstracts_reviewing_settings
from indico.modules.events.tracks import Track


@pytest.fixture
def dummy_abstract(db, dummy_event, dummy_user):
    abstract = Abstract(friendly_id=314,
                        title="Broken Symmetry and the Mass of Gauge Vector Mesons",
                        event=dummy_event,
                        submitter=dummy_user,
                        locator={'event_id': -314, 'abstract_id': 1234},
                        judgment_comment='Vague but interesting!')

    db.session.add(abstract)
    db.session.flush()
    return abstract


@pytest.mark.parametrize(('value', 'scale_min', 'scale_max', 'expected'), (
    (5, 1, 3, 3),
    (5, 0, 10, 10),
    (0, 0, 10, 0),
    (2, 0, 10, 4),
    (3, 5, 50, 32),
    (5, 5, 50, 50),
    (None, 0, 10, None)
))
def test_abstract_review_scale_ratings(db, dummy_abstract, dummy_event, dummy_user,
                                       value, scale_min, scale_max, expected):
    from indico.modules.events.abstracts.controllers.management import RHManageAbstractReviewing
    abstracts_reviewing_settings.set(dummy_event, 'scale_lower', 0)
    abstracts_reviewing_settings.set(dummy_event, 'scale_upper', 5)

    question = AbstractReviewQuestion(field_type='rating', title='Rating')
    dummy_event.abstract_review_questions.append(question)
    review = AbstractReview(
        abstract=dummy_abstract, track=Track(title='Dummy Track', event=dummy_event),
        user=dummy_user, proposed_action=AbstractAction.accept
    )
    rating = AbstractReviewRating(question=question, value=value)
    review.ratings.append(rating)
    db.session.flush()
    rh = RHManageAbstractReviewing()
    rh.event = dummy_event
    rh._scale_ratings(scale_min, scale_max)
    assert rating.value == expected
