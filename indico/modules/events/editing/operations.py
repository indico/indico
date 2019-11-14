# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.editing import logger
from indico.modules.events.editing.models.editable import Editable
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.revisions import EditingRevision, FinalRevisionState, InitialRevisionState
from indico.modules.events.editing.schemas import EditingReviewAction


def _make_editable_files(editable, files):
    if not files:
        return []
    editable_files = [
        EditingRevisionFile(file=file, file_type=file_type)
        for file_type, file_list in files.viewitems()
        for file in file_list
    ]
    for ef in editable_files:
        ef.file.claim(contrib_id=editable.contribution.id, editable_type=editable.type.name)
    return editable_files


@no_autoflush
def create_new_editable(contrib, type_, submitter, files):
    editable = Editable(contribution=contrib, type=type_)
    revision = EditingRevision(submitter=submitter,
                               initial_state=InitialRevisionState.ready_for_review,
                               files=_make_editable_files(editable, files))
    editable.revisions.append(revision)
    db.session.flush()
    logger.info('Editable [%s] created by %s for %s', type_.name, submitter, contrib)
    return editable


def publish_editable_revision(revision):
    revision.editable.published_revision = revision
    db.session.flush()
    logger.info('Revision %r marked as published', revision)


@no_autoflush
def review_editable_revision(revision, editor, action, comment, tags, files=None):
    assert revision.final_state == FinalRevisionState.none
    revision.editor = editor
    revision.comment = comment
    revision.tags = tags
    revision.final_state = {
        EditingReviewAction.accept: FinalRevisionState.accepted,
        EditingReviewAction.reject: FinalRevisionState.rejected,
        EditingReviewAction.update: FinalRevisionState.needs_submitter_confirmation,
        EditingReviewAction.request_update: FinalRevisionState.needs_submitter_changes,
    }[action]

    db.session.flush()
    if action == EditingReviewAction.accept:
        publish_editable_revision(revision)
    elif action == EditingReviewAction.update:
        new_revision = EditingRevision(submitter=editor,
                                       initial_state=InitialRevisionState.needs_submitter_confirmation,
                                       files=_make_editable_files(revision.editable, files))
        revision.editable.revisions.append(new_revision)
    db.session.flush()
    logger.info('Revision %r reviewed by %s [%s]', revision, editor, action.name)
