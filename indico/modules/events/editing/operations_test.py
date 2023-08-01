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
    rev1 = EditingRevision(editable=editable, user=dummy_user, type=RevisionType.ready_for_review)
    rev2 = EditingRevision(editable=editable, user=dummy_user, type=RevisionType.needs_submitter_confirmation)
    rev3 = EditingRevision(editable=editable, user=dummy_user, type=RevisionType.changes_rejection)
    with pytest.raises(InvalidEditableState):
        undo_review(rev1)
    with pytest.raises(InvalidEditableState):
        undo_review(rev2)
    undo_review(rev3)
    assert not rev1.is_undone
    assert not rev2.is_undone
    assert rev3.is_undone


@pytest.mark.parametrize(('type', 'ok'), (
    (RevisionType.new, False),
    (RevisionType.ready_for_review, False),
    (RevisionType.needs_submitter_changes, True),
    (RevisionType.changes_acceptance, True),
    (RevisionType.changes_rejection, True),
    (RevisionType.needs_submitter_confirmation, True),
    (RevisionType.acceptance, True),
    (RevisionType.rejection, True),
    (RevisionType.reset, True),
))
def test_can_undo_review(db, dummy_contribution, dummy_user, type, ok):
    from indico.modules.events.editing.operations import InvalidEditableState, undo_review
    editable = Editable(contribution=dummy_contribution, type=EditableType.paper)
    rev = EditingRevision(editable=editable, user=dummy_user, type=type)
    db.session.flush()

    if ok:
        undo_review(rev)
        assert rev.is_undone
    else:
        pytest.raises(InvalidEditableState, undo_review, rev)
        assert not rev.is_undone

    db.session.expire(editable)  # so a deleted revision shows up in the relationship
    if type == RevisionType.reset:
        assert len(editable.revisions) == 0
    else:
        assert len(editable.revisions) == 1
    if ok or type == RevisionType.reset:
        assert len(editable.valid_revisions) == 0
    else:
        assert len(editable.valid_revisions) == 1
