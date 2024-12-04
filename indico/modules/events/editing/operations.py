# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
from io import BytesIO
from zipfile import ZipFile

from flask import jsonify, session
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.editing import logger
from indico.modules.events.editing.models.comments import EditingRevisionComment
from indico.modules.events.editing.models.editable import Editable, EditableState
from indico.modules.events.editing.models.file_types import EditingFileType
from indico.modules.events.editing.models.review_conditions import EditingReviewCondition
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.revisions import EditingRevision, RevisionType
from indico.modules.events.editing.models.tags import EditingTag
from indico.modules.events.editing.notifications import (notify_comment, notify_editor_judgment,
                                                         notify_submitter_confirmation, notify_submitter_upload)
from indico.modules.events.editing.schemas import (EditableDumpSchema, EditingConfirmationAction, EditingFileTypeSchema,
                                                   EditingReviewAction)
from indico.modules.logs import EventLogRealm, LogKind
from indico.modules.logs.util import make_diff_log
from indico.modules.users import User
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename
from indico.util.i18n import _, orig_string
from indico.web.flask.util import send_file


FILE_TYPE_ATTRS = {
    'name': {'title': 'Name', 'type': 'string'},
    'extensions': 'Extensions',
    'allow_multiple_files': 'Multiple files',
    'required': 'File required',
    'publishable': 'Publishable',
    'filename_template': {'title': 'Filename template', 'type': 'string'},
}


class InvalidEditableState(BadRequest):
    """
    An error indicating that an operation on an Editable failed because its
    current state does not permit it, or that the provided revision hint
    did not match (ie the revisions changed in the meantime).
    """

    def __init__(self):
        super().__init__(_('The requested action is not possible on this revision'))


def ensure_latest_revision(revision):
    if revision != revision.editable.latest_revision:
        raise InvalidEditableState


def _ensure_state(revision, state):
    if isinstance(state, EditableState):
        state = {state}
    if revision.editable.state not in state:
        raise InvalidEditableState


def _make_editable_files(editable, files):
    if not files:
        return []
    editable_files = [
        EditingRevisionFile(file=file, file_type=file_type)
        for file_type, file_list in files.items()
        for file in file_list
    ]
    for ef in editable_files:
        ef.file.claim()
    return editable_files


@no_autoflush
def create_new_editable(contrib, type_, submitter, files, type=RevisionType.ready_for_review):
    editable = Editable(contribution=contrib, type=type_)
    revision = EditingRevision(user=submitter,
                               type=type,
                               files=_make_editable_files(editable, files))
    editable.revisions.append(revision)
    db.session.flush()
    logger.info('Editable [%s] created by %s for %s', type_.name, submitter, contrib)
    return editable


def delete_editable(editable, *, soft=True):
    log_msg = f'{editable.log_title} deleted'
    editable.log(EventLogRealm.reviewing, LogKind.negative, 'Editing', log_msg, session.user)
    db.session.expire(editable)
    if soft:
        editable.is_deleted = True
    else:
        for revision in editable.revisions:
            for ef in revision.files:
                ef.file.claimed = False
        db.session.delete(editable)
    db.session.flush()


def _log_review(editable, kind, log_msg, old_state=None, was_published=None):
    log_fields = {'state': 'Editable State', 'published': 'Published'}
    changes = {}
    if old_state is not None and old_state != editable.state:
        changes['state'] = (old_state, editable.state)
    if was_published is not None and was_published != (editable.published_revision is not None):
        changes['published'] = (was_published, editable.published_revision is not None)
    editable.log(EventLogRealm.reviewing, kind, 'Editing', log_msg,
                 session.user, data={'Changes': make_diff_log(changes, log_fields)})


def publish_editable_revision(revision):
    ensure_latest_revision(revision)
    was_published = revision.editable.published_revision is not None
    revision.editable.published_revision = revision
    db.session.flush()
    logger.info('Revision %r marked as published', revision)
    _log_review(revision.editable, LogKind.positive, f'{revision.editable.log_title} published',
                was_published=was_published)


@no_autoflush
def review_editable_revision(revision, editor, action, comment, tags, files=None):
    ensure_latest_revision(revision)
    _ensure_state(revision, EditableState.ready_for_review)
    revision_type = {
        EditingReviewAction.accept: RevisionType.acceptance,
        EditingReviewAction.reject: RevisionType.rejection,
        EditingReviewAction.update: RevisionType.needs_submitter_confirmation,
        EditingReviewAction.request_update: RevisionType.needs_submitter_changes,
    }[action]

    db.session.flush()
    new_revision = None
    old_state = revision.editable.state
    new_revision = EditingRevision(user=editor,
                                   type=revision_type,
                                   files=_make_editable_files(revision.editable, files) if files else [],
                                   comment=comment,
                                   tags=set(tags))
    revision.editable.revisions.append(new_revision)
    if action in (EditingReviewAction.update, EditingReviewAction.accept):
        _ensure_publishable_files(new_revision)
    submitters = revision.editable.contribution.get_manager_list(include_groups=False, permission='submit',
                                                                 explicit=True)
    db.session.flush()
    notify_editor_judgment(new_revision, submitters, action)
    logger.info('Revision %r reviewed by %s [%s]', revision, editor, action.name)
    _log_review(revision.editable, LogKind.positive, f'Revision for {revision.editable.log_title} reviewed',
                old_state=old_state)
    return new_revision


@no_autoflush
def confirm_editable_changes(revision, submitter, action, comment):
    ensure_latest_revision(revision)
    _ensure_state(revision, EditableState.needs_submitter_confirmation)
    revision_type = {
        EditingConfirmationAction.accept: RevisionType.changes_acceptance,
        EditingConfirmationAction.reject: RevisionType.changes_rejection,
    }[action]
    old_state = revision.editable.state
    new_revision = EditingRevision(user=submitter,
                                   type=revision_type,
                                   comment=comment,
                                   tags=revision.tags)
    revision.editable.revisions.append(new_revision)
    db.session.flush()
    if action == EditingConfirmationAction.accept:
        _ensure_publishable_files(revision)
    db.session.flush()
    notify_submitter_confirmation(new_revision, submitter, action)
    logger.info('Revision %r confirmed by %s [%s]', revision, submitter, action.name)
    _log_review(revision.editable, LogKind.positive, f'Revision for {revision.editable.log_title} confirmed',
                old_state=old_state)
    return new_revision


@no_autoflush
def replace_revision(revision, user, comment, files, tags):
    ensure_latest_revision(revision)
    _ensure_state(revision, {EditableState.new, EditableState.ready_for_review})
    revision.tags = tags
    new_revision = EditingRevision(user=user,
                                   type=RevisionType.replacement,
                                   comment=comment,
                                   files=_make_editable_files(revision.editable, files))
    revision.editable.revisions.append(new_revision)
    db.session.flush()
    logger.info('Revision %r replaced by %s', revision, user)
    revision.editable.log(EventLogRealm.reviewing, LogKind.change, 'Editing',
                          f'Revision for {revision.editable.log_title} replaced', user)


@no_autoflush
def create_submitter_revision(prev_revision, user, files):
    ensure_latest_revision(prev_revision)
    try:
        _ensure_state(prev_revision, EditableState.ready_for_review)
        if prev_revision.editable.editor:
            raise InvalidEditableState
    except InvalidEditableState:
        _ensure_state(prev_revision, EditableState.needs_submitter_changes)
    old_state = prev_revision.editable.state
    new_revision = EditingRevision(user=user,
                                   type=RevisionType.ready_for_review,
                                   files=_make_editable_files(prev_revision.editable, files),
                                   tags=prev_revision.tags)
    prev_revision.editable.revisions.append(new_revision)
    db.session.flush()
    notify_submitter_upload(new_revision)
    logger.info('Revision %r created by submitter %s', new_revision, user)
    _log_review(prev_revision.editable, LogKind.positive, f'Revision for {new_revision.editable.log_title} uploaded',
                old_state=old_state)
    return new_revision


def _ensure_revision_can_be_updated(revision):
    ensure_latest_revision(revision)
    if revision.editable.state in {EditableState.new, EditableState.ready_for_review}:
        raise InvalidEditableState


@no_autoflush
def undo_review(revision):
    _ensure_revision_can_be_updated(revision)
    editable = revision.editable
    old_state = editable.state
    was_published = editable.published_revision is not None
    editable.published_revision = None
    db.session.flush()
    revision.is_undone = True
    db.session.flush()
    logger.info('Revision %r review undone by %r', revision, session.user)
    _log_review(editable, LogKind.negative, f'Review on {editable.log_title} removed',
                old_state=old_state, was_published=was_published)


@no_autoflush
def update_review_comment(revision, text):
    _ensure_revision_can_be_updated(revision)
    changes = {'comment': (revision.comment, text)}
    log_fields = {'comment': 'Comment'}
    revision.comment = text
    revision.modified_dt = now_utc()
    db.session.flush()
    logger.info('Review comment on revision %r updated by %r', revision, session.user)
    revision.editable.log(EventLogRealm.reviewing, LogKind.change, 'Editing',
                          f'Review comment on {revision.editable.log_title} updated',
                          session.user, data={'Changes': make_diff_log(changes, log_fields)})


@no_autoflush
def reset_editable(revision):
    _ensure_revision_can_be_updated(revision)
    editable = revision.editable
    old_state = editable.state
    if old_state != EditableState.accepted:
        return
    was_published = editable.published_revision is not None
    editable.published_revision = None
    db.session.flush()
    new_revision = EditingRevision(user=User.get_system_user(), type=RevisionType.reset, tags=revision.tags)
    editable.revisions.append(new_revision)
    db.session.flush()
    logger.info('Revision %r review reset', revision)
    _log_review(editable, LogKind.negative, f'State of {editable.log_title} reset',
                old_state=old_state, was_published=was_published)


@no_autoflush
def create_revision_comment(revision, user, text, internal=False):
    ensure_latest_revision(revision)
    comment = EditingRevisionComment(user=user, text=text, internal=internal)
    revision.comments.append(comment)
    db.session.flush()
    notify_comment(comment)
    logger.info('Comment on revision %r created by %r: %r', revision, user, comment)
    revision.editable.log(EventLogRealm.reviewing, LogKind.positive, 'Editing',
                          f'Comment on {revision.editable.log_title} created', session.user)


@no_autoflush
def update_revision_comment(comment, updates):
    ensure_latest_revision(comment.revision)
    changes = comment.populate_from_dict(updates)
    comment.modified_dt = now_utc()
    db.session.flush()
    logger.info('Comment on revision %r updated: %r', comment.revision, comment)
    log_fields = {'text': 'Text', 'internal': 'Restricted to editors'}
    comment.revision.editable.log(EventLogRealm.reviewing, LogKind.change, 'Editing',
                                  f'Comment on {comment.revision.editable.log_title} updated',
                                  session.user, data={'Changes': make_diff_log(changes, log_fields)})


@no_autoflush
def delete_revision_comment(comment):
    ensure_latest_revision(comment.revision)
    comment.is_deleted = True
    db.session.flush()
    logger.info('Comment on revision %r deleted: %r', comment.revision, comment)
    comment.revision.editable.log(EventLogRealm.reviewing, LogKind.negative, 'Editing',
                                  f'Comment on {comment.revision.editable.log_title} deleted',
                                  session.user)


def create_new_tag(event, code, title, color, system=False):
    tag = EditingTag(code=code, title=title, color=color, system=system, event=event)
    db.session.flush()
    logger.info('Tag %r created by %r', tag, session.user)
    tag.log(EventLogRealm.management, LogKind.positive, 'Editing', f'Tag {tag.verbose_title} created', session.user)
    return tag


def update_tag(tag, updates):
    changes = tag.populate_from_dict({k: v for k, v in updates.items() if v is not None})
    db.session.flush()
    logger.info('Tag %r updated by %r', tag, session.user)
    log_fields = {
        'code': {'title': 'Code', 'type': 'string'},
        'title': {'title': 'Title', 'type': 'string'},
        'color': {'title': 'Color', 'type': 'string'},
    }
    tag.log(EventLogRealm.management, LogKind.change, 'Editing', f'Tag {tag.verbose_title} updated', session.user,
            data={'Changes': make_diff_log(changes, log_fields)})


def delete_tag(tag):
    logger.info('Tag %r deleted by %r', tag, session.user)
    tag.log(EventLogRealm.management, LogKind.negative, 'Editing', f'Tag {tag.verbose_title} deleted', session.user)
    db.session.delete(tag)


def create_new_file_type(event, editable_type, **data):
    file_type = EditingFileType(event=event, type=editable_type)
    file_type.populate_from_dict(data, keys=FILE_TYPE_ATTRS)
    db.session.flush()
    logger.info('File type %r for %s created by %r', file_type, editable_type.name, session.user)
    file_type.log(EventLogRealm.management, LogKind.positive, 'Editing', f'File type {file_type.name} created',
                  session.user)
    return file_type


def update_file_type(file_type, **data):
    changes = file_type.populate_from_dict(data, keys=FILE_TYPE_ATTRS)
    db.session.flush()
    logger.info('File type %r updated by %r', file_type, session.user)
    file_type.log(EventLogRealm.management, LogKind.change, 'Editing', f'File type {file_type.name} updated',
                  session.user, data={'Changes': make_diff_log(changes, FILE_TYPE_ATTRS)})


def delete_file_type(file_type):
    logger.info('File type %r deleted by %r', file_type, session.user)
    file_type.log(EventLogRealm.management, LogKind.negative, 'Editing', f'File type {file_type.name} deleted',
                  session.user)
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
    old_editor = editable.editor
    editable.editor = editor
    logger.info('Editable %r assigned to editor %r', editable, editor)
    log_data = {
        'Editor': editor.full_name,
        'Editable type': orig_string(editable.type.title),
        'Editable': editable.contribution.title
    }
    if old_editor:
        log_data['Previous editor'] = old_editor.full_name
    log_msg = f'{editable.log_title} assigned to {editor.full_name}'
    editable.log(EventLogRealm.management, LogKind.positive, 'Editing', log_msg, session.user, data=log_data)
    db.session.flush()


def unassign_editor(editable):
    if not (editor := editable.editor):
        return
    editable.editor = None
    logger.info('Editor %r has been unassigned from %r', editor, editable)
    log_data = {
        'Editor': editor.full_name,
        'Editable type': orig_string(editable.type.title),
        'Editable': editable.contribution.title
    }
    log_msg = f'{editable.log_title} unassigned from {editor.full_name}'
    editable.log(EventLogRealm.management, LogKind.negative, 'Editing', log_msg, session.user, data=log_data)
    db.session.flush()


def generate_editables_zip(event, editable_type, editables):
    buf = BytesIO()
    with ZipFile(buf, 'w', allowZip64=True) as zip_file:
        for editable in editables:
            for revision_file in editable.latest_revision.files:
                file_obj = revision_file.file
                with file_obj.get_local_path() as src_file:
                    zip_file.write(src_file, _compose_filepath(editable, revision_file))

    buf.seek(0)
    return send_file('files.zip', buf, 'application/zip', inline=False)


def generate_editables_json(event, editable_type, editables):
    file_types = EditingFileType.query.with_parent(event).filter_by(type=editable_type).all()
    file_types_dump = EditingFileTypeSchema(many=True).dump(file_types)
    editables_dump = EditableDumpSchema(many=True, context={'include_emails': True}).dump(editables)
    response = jsonify(version=1, file_types=file_types_dump, editables=editables_dump)
    response.headers['Content-Disposition'] = 'attachment; filename="editables.json"'
    return response


def _compose_filepath(editable, revision_file):
    file_obj = revision_file.file
    contrib = editable.contribution
    editable_type = editable.type.name
    code = f'Editable-{contrib.friendly_id}'

    if contrib.code:
        code += f'-{contrib.code}'

    filepath = os.path.join(secure_filename(f'{contrib.title}-{contrib.id}',
                                            f'contribution-{contrib.id}'),
                            editable_type, code, revision_file.file_type.name)
    filename, ext = os.path.splitext(file_obj.filename)
    filename = secure_filename(file_obj.filename,
                               f'revision-file-{revision_file.revision_id}-{file_obj.id}{ext}')
    return os.path.join(filepath, filename)


def _ensure_publishable_files(revision):
    if not revision.editable.latest_revision_with_files.has_publishable_files:
        raise InvalidEditableState
