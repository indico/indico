# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session
from werkzeug.exceptions import ServiceUnavailable

from indico.modules.events.editing.operations import (confirm_editable_changes, publish_editable_revision,
                                                      review_editable_revision)
from indico.modules.events.editing.schemas import EditingConfirmationAction, EditingReviewAction
from indico.modules.events.editing.service import ServiceRequestFailed, service_handle_review_editable
from indico.modules.events.editing.settings import editing_settings
from indico.util.i18n import _


def review_and_publish_editable(revision, action, comment, tags=frozenset(), files=None):
    service_url = editing_settings.get(revision.editable.event, 'service_url')
    new_revision = review_editable_revision(revision, session.user, action, comment, tags, files)
    publish = True
    if service_url:
        try:
            resp = service_handle_review_editable(revision.editable, session.user, action, revision, new_revision)
            publish = resp.get('publish', True)
        except ServiceRequestFailed:
            raise ServiceUnavailable(_('Failed processing review, please try again later.'))
    if publish and action == EditingReviewAction.accept:
        publish_editable_revision(new_revision or revision)


def confirm_and_publish_changes(revision, action, comment):
    new_revision = confirm_editable_changes(revision, session.user, action, comment)
    service_url = editing_settings.get(revision.editable.event, 'service_url')
    publish = True
    if service_url:
        try:
            resp = service_handle_review_editable(revision.editable, session.user, action, revision, new_revision)
            publish = resp.get('publish', True)
        except ServiceRequestFailed:
            raise ServiceUnavailable(_('Failed processing review, please try again later.'))
    if publish and action == EditingConfirmationAction.accept:
        publish_editable_revision(new_revision or revision)
