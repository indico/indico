# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.editing.models.editable import Editable, EditableType
from indico.modules.events.editing.models.revisions import EditingRevision, RevisionType


def test_cannot_undo_review_old_rev(dummy_contribution, dummy_user):
    from indico.modules.events.editing.operations import InvalidEditableState, undo_review
    editable = Editable(contribution=dummy_contribution, type=EditableType.paper)
    rev1 = EditingRevision(editable=editable, submitter=dummy_user,
                           type=RevisionType.ready_for_review)
    rev2 = EditingRevision(editable=editable, submitter=dummy_user,
                           type=RevisionType.needs_submitter_confirmation)
    rev3 = EditingRevision(editable=editable, submitter=dummy_user,
                           type=RevisionType.needs_submitter_changes)
    with pytest.raises(InvalidEditableState):
        undo_review(rev1)
    with pytest.raises(InvalidEditableState):
        undo_review(rev2)
    undo_review(rev3)


@pytest.mark.parametrize(('t1', 'ok1', 't2', 'ok2'), (
    (RevisionType.ready_for_review, RevisionType.accepted, True,
     None, None, None),

    (RevisionType.ready_for_review, RevisionType.rejected, True,
     None, None, None),

    (RevisionType.ready_for_review, RevisionType.needs_submitter_changes, True,
     None, None, None),

    (RevisionType.ready_for_review, RevisionType.needs_submitter_confirmation, True,
     RevisionType.needs_submitter_confirmation, RevisionType.none, False),

    (RevisionType.ready_for_review, RevisionType.needs_submitter_confirmation, False,
     RevisionType.needs_submitter_confirmation, RevisionType.accepted, True),

    (RevisionType.ready_for_review, RevisionType.needs_submitter_confirmation, False,
     RevisionType.needs_submitter_confirmation, RevisionType.needs_submitter_changes, True),

    (RevisionType.ready_for_review, RevisionType.needs_submitter_changes, False,
     RevisionType.ready_for_review, RevisionType.none, False),

    (RevisionType.ready_for_review, RevisionType.needs_submitter_changes, False,
     RevisionType.ready_for_review, RevisionType.needs_submitter_changes, True),
))
def test_can_undo_review(db, dummy_contribution, dummy_user, t1, ok1, t2, ok2):
    from indico.modules.events.editing.operations import InvalidEditableState, undo_review
    editable = Editable(contribution=dummy_contribution, type=EditableType.paper)
    rev1 = EditingRevision(editable=editable, submitter=dummy_user, type=t1)
    if t2 is not None:
        rev2 = EditingRevision(editable=editable, submitter=dummy_user, type=t2)
    db.session.flush()

    if ok1:
        undo_review(rev1)
    else:
        pytest.raises(InvalidEditableState, undo_review, rev1)

    if t2 is not None:
        if ok2:
            undo_review(rev2)
        else:
            pytest.raises(InvalidEditableState, undo_review, rev2)

    db.session.expire(editable)  # so a deleted revision shows up in the relationship
    if ok1:
        assert rev1.final_state == RevisionType.none
        if t2 is None:
            assert len(editable.revisions) == 1
        else:
            assert rev2.final_state == RevisionType.undone
            assert len(editable.revisions) == 2
    elif ok2:
        assert rev2.final_state == RevisionType.none
        assert len(editable.revisions) == 2


def test_can_undo_review_request_changes(db, dummy_contribution, dummy_user):
    from indico.modules.events.editing.operations import InvalidEditableState, undo_review
    editable = Editable(contribution=dummy_contribution, type=EditableType.paper)
    rev1 = EditingRevision(editable=editable, submitter=dummy_user,
                           type=RevisionType.ready_for_review)
    rev2 = EditingRevision(editable=editable, submitter=dummy_user, editor=dummy_user,
                           type=RevisionType.needs_submitter_changes)
    db.session.flush()

    with pytest.raises(InvalidEditableState):
        undo_review(rev1)
    undo_review(rev2)

    db.session.expire(editable)  # so a deleted revision shows up in the relationship
    assert not rev1.is_undone
    assert rev2.is_undone
    assert len(editable.revisions) == 2
