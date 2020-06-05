# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import os
from io import BytesIO
from zipfile import ZipFile

from flask import session
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.editing import logger
from indico.modules.events.editing.models.comments import EditingRevisionComment
from indico.modules.events.editing.models.editable import Editable
from indico.modules.events.editing.models.file_types import EditingFileType
from indico.modules.events.editing.models.review_conditions import EditingReviewCondition
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.revisions import EditingRevision, FinalRevisionState, InitialRevisionState
from indico.modules.events.editing.models.tags import EditingTag
from indico.modules.events.editing.notifications import (notify_comment, notify_editor_judgment,
                                                         notify_submitter_confirmation, notify_submitter_upload)
from indico.modules.events.editing.schemas import EditingConfirmationAction, EditingReviewAction
from indico.modules.events.logs import EventLogKind, EventLogRealm
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.web.flask.util import send_file


FILE_TYPE_ATTRS = ('name', 'extensions', 'allow_multiple_files', 'required', 'publishable', 'filename_template')


class InvalidEditableState(BadRequest):
    """
    An error indicating that an operation on an Editable failed because its
    current state does not permit it, or that the provided revision hint
    did not match (ie the revisions changed in the meantime).
    """

    def __init__(self):
        super(InvalidEditableState, self).__init__(_('The requested action is not possible on this revision'))


def _ensure_latest_revision(revision):
    if revision != revision.editable.revisions[-1]:
        raise InvalidEditableState


def _ensure_state(revision, initial=None, final=None):
    if isinstance(initial, InitialRevisionState):
        initial = {initial}
    if isinstance(final, FinalRevisionState):
        final = {final}
    if initial is not None and revision.initial_state not in initial:
        raise InvalidEditableState
    if final is not None and revision.final_state not in final:
        raise InvalidEditableState


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
    _ensure_latest_revision(revision)
    revision.editable.published_revision = revision
    db.session.flush()
    logger.info('Revision %r marked as published', revision)


@no_autoflush
def review_editable_revision(revision, editor, action, comment, tags, files=None):
    _ensure_latest_revision(revision)
    _ensure_state(revision, initial=InitialRevisionState.ready_for_review, final=FinalRevisionState.none)
    revision.editor = editor
    revision.comment = comment
    revision.tags = tags
    revision.final_state = {
        EditingReviewAction.accept: FinalRevisionState.accepted,
        EditingReviewAction.reject: FinalRevisionState.rejected,
        EditingReviewAction.update: FinalRevisionState.needs_submitter_confirmation,
        EditingReviewAction.update_accept: FinalRevisionState.needs_submitter_confirmation,
        EditingReviewAction.request_update: FinalRevisionState.needs_submitter_changes,
    }[action]

    db.session.flush()
    if action == EditingReviewAction.accept:
        _ensure_publishable_files(revision)
        publish_editable_revision(revision)
    elif action in (EditingReviewAction.update, EditingReviewAction.update_accept):
        final_state = FinalRevisionState.none
        editable_editor = None
        if action == EditingReviewAction.update_accept:
            final_state = FinalRevisionState.accepted
            editable_editor = editor
        new_revision = EditingRevision(submitter=editor,
                                       editor=editable_editor,
                                       initial_state=InitialRevisionState.needs_submitter_confirmation,
                                       final_state=final_state,
                                       files=_make_editable_files(revision.editable, files),
                                       tags=revision.tags)
        _ensure_publishable_files(new_revision)
        revision.editable.revisions.append(new_revision)
    db.session.flush()
    notify_editor_judgment(revision, session.user)
    logger.info('Revision %r reviewed by %s [%s]', revision, editor, action.name)


@no_autoflush
def confirm_editable_changes(revision, submitter, action, comment):
    _ensure_latest_revision(revision)
    _ensure_state(revision, initial=InitialRevisionState.needs_submitter_confirmation, final=FinalRevisionState.none)
    revision.final_state = {
        EditingConfirmationAction.accept: FinalRevisionState.accepted,
        EditingConfirmationAction.reject: FinalRevisionState.needs_submitter_changes,
    }[action]
    if comment:
        revision.comment = comment
    db.session.flush()
    if action == EditingConfirmationAction.accept:
        _ensure_publishable_files(revision)
        publish_editable_revision(revision)
    db.session.flush()
    notify_submitter_confirmation(revision, submitter, action)
    logger.info('Revision %r confirmed by %s [%s]', revision, submitter, action.name)


@no_autoflush
def replace_revision(revision, user, comment, files):
    _ensure_latest_revision(revision)
    _ensure_state(revision,
                  initial=(InitialRevisionState.new, InitialRevisionState.ready_for_review),
                  final=FinalRevisionState.none)
    revision.comment = comment
    revision.final_state = FinalRevisionState.replaced
    new_revision = EditingRevision(submitter=user,
                                   initial_state=revision.initial_state,
                                   files=_make_editable_files(revision.editable, files))
    revision.editable.revisions.append(new_revision)
    db.session.flush()
    logger.info('Revision %r replaced by %s', revision, user)


@no_autoflush
def create_submitter_revision(prev_revision, user, files):
    _ensure_latest_revision(prev_revision)
    _ensure_state(prev_revision, final=FinalRevisionState.needs_submitter_changes)
    new_revision = EditingRevision(submitter=user,
                                   initial_state=InitialRevisionState.ready_for_review,
                                   files=_make_editable_files(prev_revision.editable, files),
                                   tags=prev_revision.tags)
    prev_revision.editable.revisions.append(new_revision)
    db.session.flush()
    notify_submitter_upload(new_revision)
    logger.info('Revision %r created by submitter %s', new_revision, user)


def _ensure_latest_revision_with_final_state(revision):
    expected = next((r for r in revision.editable.revisions[::-1] if r.final_state != FinalRevisionState.none), None)
    if revision != expected:
        raise InvalidEditableState


@no_autoflush
def undo_review(revision):
    _ensure_latest_revision_with_final_state(revision)
    latest_revision = revision.editable.revisions[-1]
    if revision != latest_revision:
        if revision.editable.revisions[-2:] != [revision, latest_revision]:
            raise InvalidEditableState
        _ensure_state(revision, final=FinalRevisionState.needs_submitter_confirmation)
        _ensure_state(latest_revision,
                      initial=InitialRevisionState.needs_submitter_confirmation,
                      final=FinalRevisionState.none)
        db.session.delete(latest_revision)
    if (revision.initial_state == InitialRevisionState.needs_submitter_confirmation and
            revision.final_state == FinalRevisionState.accepted and revision.editor is not None):
        revision = revision.editable.revisions[-2]
        db.session.delete(latest_revision)
    elif revision.final_state == FinalRevisionState.accepted:
        revision.editable.published_revision = None
    db.session.flush()
    revision.final_state = FinalRevisionState.none
    revision.comment = ''
    db.session.flush()
    logger.info('Revision %r review undone', revision)


@no_autoflush
def create_revision_comment(revision, user, text, internal=False):
    _ensure_latest_revision(revision)
    comment = EditingRevisionComment(user=user, text=text, internal=internal)
    revision.comments.append(comment)
    db.session.flush()
    notify_comment(comment)
    logger.info('Comment on revision %r created by %r: %r', revision, user, comment)


@no_autoflush
def update_revision_comment(comment, updates):
    _ensure_latest_revision(comment.revision)
    comment.populate_from_dict(updates)
    comment.modified_dt = now_utc()
    db.session.flush()
    logger.info('Comment on revision %r updated: %r', comment.revision, comment)


@no_autoflush
def delete_revision_comment(comment):
    _ensure_latest_revision(comment.revision)
    comment.is_deleted = True
    db.session.flush()
    logger.info('Comment on revision %r deleted: %r', comment.revision, comment)


def create_new_tag(event, code, title, color, system=False):
    tag = EditingTag(code=code, title=title, color=color, system=system, event=event)
    db.session.flush()
    logger.info('Tag %r created by %r', tag, session.user)
    return tag


def update_tag(tag, code=None, title=None, color=None):
    if code:
        tag.code = code
    if title:
        tag.title = title
    if color:
        tag.color = color
    db.session.flush()
    logger.info('Tag %r updated by %r', tag, session.user)


def delete_tag(tag):
    logger.info('Tag %r deleted by %r', tag, session.user)
    db.session.delete(tag)


def create_new_file_type(event, editable_type, **data):
    file_type = EditingFileType(event=event, type=editable_type)
    file_type.populate_from_dict(data, keys=FILE_TYPE_ATTRS)
    db.session.flush()
    logger.info('File type %r for %s created by %r', file_type, editable_type.name, session.user)
    return file_type


def update_file_type(file_type, **data):
    file_type.populate_from_dict(data, keys=FILE_TYPE_ATTRS)
    db.session.flush()
    logger.info('File type %r updated by %r', file_type, session.user)


def delete_file_type(file_type):
    logger.info('File type %r deleted by %r', file_type, session.user)
    db.session.delete(file_type)


def create_new_review_condition(event, editable_type, file_types):
    review_condition = EditingReviewCondition(event=event, type=editable_type, file_types=file_types)
    db.session.flush()
    logger.info('Review condition %r created by %r', review_condition, session.user)
    return review_condition


def update_review_condition(condition, file_types):
    condition.file_types = file_types
    db.session.flush()
    logger.info('Review condition %r updated by %r', condition, session.user)


def delete_review_condition(condition):
    logger.info('Review condition %r deleted by %r', condition, session.user)
    db.session.delete(condition)


def assign_editor(editable, editor):
    editable.editor = editor
    logger.info('Editable %r assigned to editor %r', editable, editor)
    editable.event.log(EventLogRealm.management, EventLogKind.change, 'Editing',
                       'Editable assigned to an editor', session.user, data={'Editor': editor.full_name})
    db.session.flush()


def unassign_editor(editable):
    editor = editable.editor
    editable.editor = None
    logger.info('Editor %r has been unassigned from %r', editor, editable)
    editable.event.log(EventLogRealm.management, EventLogKind.change, 'Editing',
                       'Editable has been unassigned from the editor', session.user,
                       data={'Unassigned from': editor.full_name})
    db.session.flush()


def generate_editables_zip(editables):
    buf = BytesIO()
    with ZipFile(buf, 'w', allowZip64=True) as zip_file:
        for editable in editables:
            for revision_file in editable.revisions[-1].files:
                file_obj = revision_file.file
                with file_obj.get_local_path() as src_file:
                    zip_file.write(src_file, _compose_filepath(editable, revision_file))

    buf.seek(0)
    return send_file('files.zip', buf, 'application/zip', inline=False)


def _compose_filepath(editable, revision_file):
    file_obj = revision_file.file
    contrib = editable.contribution
    editable_type = editable.type.name
    code = 'Editable-{}'.format(contrib.friendly_id)

    if contrib.code:
        code += '-{}'.format(contrib.code)

    filepath = os.path.join(secure_filename('{}-{}'.format(contrib.title, contrib.id),
                                            'contribution-{}'.format(contrib.id)),
                            editable_type, code, revision_file.file_type.name)
    filename, ext = os.path.splitext(file_obj.filename)
    filename = secure_filename(file_obj.filename,
                               'revision-file-{}-{}{}'.format(revision_file.revision_id, file_obj.id, ext))
    return os.path.join(filepath, filename)


def _ensure_publishable_files(revision):
    if not any(f.file_type.publishable for f in revision.files):
        raise InvalidEditableState
