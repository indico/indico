# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime

import pytest

from indico.modules.events.papers.models.revisions import PaperRevision, PaperRevisionState
from indico.modules.events.papers.settings import paper_reviewing_settings
from indico.util.date_time import localize_as_utc, now_utc


@pytest.mark.usefixtures('dummy_contribution')
def test_can_judge(dummy_paper, dummy_user, dummy_event):
    assert not dummy_paper.can_judge(None)

    # Judged papers cannot be judged again
    PaperRevision(paper=dummy_paper, submitter=dummy_user)
    dummy_paper.state = PaperRevisionState.accepted
    dummy_paper.last_revision.judge = dummy_user
    dummy_paper.last_revision.judgment_dt = now_utc()
    assert not dummy_paper.can_judge(dummy_user, check_state=True)

    # Make sure enforced judging deadline is respected
    dummy_paper.reset_state()
    paper_reviewing_settings.set(dummy_event, 'enforce_judge_deadline', True)
    paper_reviewing_settings.set(dummy_event, 'judge_deadline', localize_as_utc(datetime(2020, 1, 1, 0, 0, 0)))
    assert not dummy_paper.can_judge(dummy_user)
    assert not dummy_paper.can_judge(dummy_user, check_state=True)

    # Allow judging if the deadline is not enforced
    paper_reviewing_settings.set(dummy_event, 'enforce_judge_deadline', False)
    dummy_event.update_principal(dummy_user, full_access=True)
    assert dummy_paper.can_judge(dummy_user)
    assert dummy_paper.can_judge(dummy_user, check_state=True)

    # Allow judging if the user can manage the paper
    paper_reviewing_settings.set(dummy_event, 'judge_deadline', None)
    assert dummy_paper.can_judge(dummy_user)
    assert dummy_paper.can_judge(dummy_user, check_state=True)

    # Allow judging if the user is a judge for the paper
    dummy_event.update_principal(dummy_user, full_access=False)
    dummy_paper.contribution.paper_judges.add(dummy_user)
    assert dummy_paper.can_judge(dummy_user)
    assert dummy_paper.can_judge(dummy_user, check_state=True)
