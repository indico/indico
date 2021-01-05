# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import pytest

from indico.modules.events.editing.models.editable import Editable, EditableType
from indico.modules.events.editing.models.revisions import EditingRevision, FinalRevisionState, InitialRevisionState


def test_cannot_undo_review_old_rev(dummy_contribution, dummy_user):
    from indico.modules.events.editing.operations import InvalidEditableState, undo_review
    editable = Editable(contribution=dummy_contribution, type=EditableType.paper)
    rev1 = EditingRevision(editable=editable, submitter=dummy_user,
                           initial_state=InitialRevisionState.ready_for_review,
                           final_state=FinalRevisionState.needs_submitter_confirmation)
    rev2 = EditingRevision(editable=editable, submitter=dummy_user,
                           initial_state=InitialRevisionState.needs_submitter_confirmation,
                           final_state=FinalRevisionState.needs_submitter_changes)
    rev3 = EditingRevision(editable=editable, submitter=dummy_user,
                           initial_state=InitialRevisionState.ready_for_review)
    with pytest.raises(InvalidEditableState):
        undo_review(rev1)
    with pytest.raises(InvalidEditableState):
        undo_review(rev2)
    undo_review(rev3)


@pytest.mark.parametrize(('is1', 'fs1', 'ok1', 'is2', 'fs2', 'ok2'), (
    (InitialRevisionState.ready_for_review, FinalRevisionState.accepted, True,
     None, None, None),

    (InitialRevisionState.ready_for_review, FinalRevisionState.rejected, True,
     None, None, None),

    (InitialRevisionState.ready_for_review, FinalRevisionState.needs_submitter_changes, True,
     None, None, None),

    (InitialRevisionState.ready_for_review, FinalRevisionState.needs_submitter_confirmation, True,
     InitialRevisionState.needs_submitter_confirmation, FinalRevisionState.none, False),

    (InitialRevisionState.ready_for_review, FinalRevisionState.needs_submitter_confirmation, False,
     InitialRevisionState.needs_submitter_confirmation, FinalRevisionState.accepted, True),

    (InitialRevisionState.ready_for_review, FinalRevisionState.needs_submitter_confirmation, False,
     InitialRevisionState.needs_submitter_confirmation, FinalRevisionState.needs_submitter_changes, True),

    (InitialRevisionState.ready_for_review, FinalRevisionState.needs_submitter_changes, False,
     InitialRevisionState.ready_for_review, FinalRevisionState.none, False),
))
def test_can_undo_review(db, dummy_contribution, dummy_user, is1, fs1, ok1, is2, fs2, ok2):
    from indico.modules.events.editing.operations import InvalidEditableState, undo_review
    editable = Editable(contribution=dummy_contribution, type=EditableType.paper)
    rev1 = EditingRevision(editable=editable, submitter=dummy_user, initial_state=is1, final_state=fs1)
    if is2 is not None:
        rev2 = EditingRevision(editable=editable, submitter=dummy_user, initial_state=is2, final_state=fs2)
    db.session.flush()

    if ok1:
        undo_review(rev1)
    else:
        pytest.raises(InvalidEditableState, undo_review, rev1)

    if is2 is not None:
        if ok2:
            undo_review(rev2)
        else:
            pytest.raises(InvalidEditableState, undo_review, rev2)

    db.session.expire(editable)  # so a deleted revision shows up in the relationship
    if ok1:
        assert rev1.final_state == FinalRevisionState.none
        assert len(editable.revisions) == 1
    elif ok2:
        assert rev2.final_state == FinalRevisionState.none
        assert len(editable.revisions) == 2
