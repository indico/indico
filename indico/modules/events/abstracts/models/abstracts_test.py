# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from sqlalchemy.inspection import inspect

from indico.modules.events.abstracts.models.abstracts import AbstractState, EditTrackMode
from indico.modules.events.abstracts.models.reviews import AbstractAction, AbstractReview
from indico.modules.events.tracks import Track


@pytest.mark.parametrize(('state', 'edit_track_mode'), (
    (AbstractState.submitted, EditTrackMode.both),
    (AbstractState.withdrawn, EditTrackMode.both),
    (AbstractState.accepted, EditTrackMode.none),
    (AbstractState.rejected, EditTrackMode.none),
    (AbstractState.merged, EditTrackMode.none),
    (AbstractState.duplicate, EditTrackMode.none),
    (AbstractState.invited, EditTrackMode.both),
))
def test_abstract_edit_track_mode(dummy_abstract, dummy_event, dummy_user, state, edit_track_mode):
    assert inspect(dummy_abstract).persistent

    dummy_abstract.state = state
    assert dummy_abstract.edit_track_mode == edit_track_mode

    if dummy_abstract.state == AbstractState.submitted:
        dummy_abstract.reviews.append(
            AbstractReview(
                track=Track(title='Dummy Track', event=dummy_event),
                user=dummy_user, proposed_action=AbstractAction.accept
            )
        )
        assert dummy_abstract.edit_track_mode == EditTrackMode.reviewed_for
