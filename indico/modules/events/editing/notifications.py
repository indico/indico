# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.notifications import make_email, send_email
from indico.modules.events.editing.schemas import EditingConfirmationAction
from indico.web.flask.templating import get_template_module


def _get_commenting_users(revision, check_internal_access=False):
    return {
        c.user
        for c in revision.comments
        if not check_internal_access or revision.editable.can_use_internal_comments(c.user)
    }


def notify_comment(comment):
    """Notify about a new comments on a revision."""
    revision = comment.revision
    editor = revision.editable.editor
    author = comment.user
    if comment.internal:
        # internal comments notify the editor and anyone who commented + can see internal comments
        recipients = _get_commenting_users(revision, check_internal_access=True) | {editor}
    elif author == editor:
        # editor comments notify the submitter and anyone else who commented
        recipients = _get_commenting_users(revision) | {revision.submitter}
    elif revision.editable.can_perform_submitter_actions(author):
        # submitter comments notify the editor and anyone else who commented
        recipients = _get_commenting_users(revision) | {editor}
    else:
        # comments from someone else (managers) notify everyone
        recipients = _get_commenting_users(revision) | {editor, revision.submitter}

    recipients.discard(None)  # in case there's no editor assigned
    recipients.discard(author)  # never bother people about their own comments
    for recipient in recipients:
        tpl = get_template_module('events/editing/emails/comment_notification.txt',
                                  author_name=author.first_name,
                                  timeline_url=revision.editable.external_timeline_url,
                                  recipient_name=recipient.first_name)
        send_email(make_email(recipient.email, template=tpl))


def notify_editor_judgment(revision, editor):
    """Notify the submitter about a judgment made by an editor."""
    submitter = revision.submitter
    tpl = get_template_module('events/editing/emails/editor_judgment_notification.txt',
                              editor_name=editor.first_name,
                              timeline_url=revision.editable.external_timeline_url,
                              recipient_name=submitter.first_name)
    send_email(make_email(submitter.email, template=tpl))


def notify_submitter_upload(revision):
    """Notify the editor about the submitter uploading a new revision."""
    submitter = revision.submitter
    editor = revision.editable.editor
    if not editor:
        return
    tpl = get_template_module('events/editing/emails/submitter_upload_notification.txt',
                              submitter_name=submitter.first_name,
                              timeline_url=revision.editable.external_timeline_url,
                              recipient_name=editor.first_name)
    send_email(make_email(editor.email, template=tpl))


def notify_submitter_confirmation(revision, submitter, action):
    """Notify the editor(s) about submitter accepting/rejecting revision changes."""
    editable = revision.editable
    current_editor = editable.editor
    prev_revision_editor = editable.revisions[-2].editor
    recipients = {current_editor, prev_revision_editor}
    recipients.discard(None)
    if action == EditingConfirmationAction.accept:
        template_path = 'events/editing/emails/submitter_confirmation_notification.txt'
    else:
        template_path = 'events/editing/emails/submitter_rejection_notification.txt'
    for recipient in recipients:
        tpl = get_template_module(template_path,
                                  submitter_name=submitter.first_name,
                                  timeline_url=revision.editable.external_timeline_url,
                                  recipient_name=recipient.first_name)
        send_email(make_email(recipient.email, template=tpl))
