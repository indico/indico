# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.categories import logger
from indico.modules.categories.models.categories import Category
from indico.modules.categories.util import format_visibility
from indico.modules.logs.models.entries import CategoryLogRealm, LogKind
from indico.modules.logs.util import make_diff_log
from indico.modules.categories.models.event_move_request import MoveRequestState


def create_category(parent, data):
    category = Category(parent=parent)
    data.setdefault('default_event_themes', parent.default_event_themes)
    data.setdefault('timezone', parent.timezone)
    category.populate_from_dict(data)
    db.session.add(category)
    db.session.flush()
    signals.category.created.send(category)
    logger.info('Category %s created by %s', category, session.user)
    sep = ' \N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK} '
    category.log(CategoryLogRealm.category, LogKind.positive, 'Category', 'Category created', session.user,
                 data={'Location': sep.join(category.chain_titles[:-1])})
    parent.log(CategoryLogRealm.category, LogKind.positive, 'Content', f'Subcategory created: "{category.title}"',
               session.user)
    return category


def delete_category(category):
    category.is_deleted = True
    db.session.flush()
    signals.category.deleted.send(category)
    logger.info('Category %s deleted by %s', category, session.user)
    category.log(CategoryLogRealm.category, LogKind.negative, 'Category', 'Category deleted', session.user)
    category.parent.log(CategoryLogRealm.category, LogKind.negative, 'Content',
                        f'Subcategory deleted: "{category.title}"', session.user)


def move_category(category, target_category):
    category.move(target_category)
    logger.info('Category %s moved to %s by %s', category, target_category, session.user)


def update_category(category, data, skip=()):
    assert set(data) <= {
        'title', 'description', 'timezone', 'suggestions_disabled', 'is_flat_view_enabled',
        'event_message_mode', 'event_message', 'notify_managers', 'event_creation_notification_emails',
        *skip
    }
    changes = category.populate_from_dict(data, skip=skip)
    db.session.flush()
    signals.category.updated.send(category)
    logger.info('Category %s updated with %r by %s', category, data, session.user)
    _log_category_update(category, changes)


def update_category_protection(category, data):
    assert set(data) <= {'protection_mode', 'own_no_access_contact', 'event_creation_restricted', 'visibility', 'event_requires_approval'}
    changes = category.populate_from_dict(data)
    db.session.flush()
    signals.category.updated.send(category, changes=changes)
    logger.info('Protection of category %r updated with %r by %r', category, data, session.user)
    if changes:
        log_fields = {'protection_mode': 'Protection mode',
                      'own_no_access_contact': 'No access contact',
                      'visibility': {'title': 'Visibility', 'type': 'string',
                                     'convert': lambda changes: [format_visibility(category, x) for x in changes]},
                      'event_creation_restricted': 'Event creation restricted',
                      'event_requires_approval': 'Event requires approval'}
        category.log(CategoryLogRealm.category, LogKind.change, 'Category', 'Protection updated', session.user,
                     data={'Changes': make_diff_log(changes, log_fields)})


def _log_category_update(category, changes):
    log_fields = {
        'title': {'title': 'Title', 'type': 'string'},
        'description': 'Description',
        'timezone': {'title': 'Timezone', 'type': 'string'},
        'suggestions_disabled': 'Disable suggestions',
        'is_flat_view_enabled': 'Allow flat view',
        'event_message_mode': 'Event header message type',
        'event_message': 'Event header message',
        'notify_managers': 'Notify managers about event creation',
        'event_creation_notification_emails': 'Event creation notification emails'
    }
    if changes:
        what = 'Settings'
        if len(changes) == 1:
            what = log_fields[list(changes)[0]]
            if isinstance(what, dict):
                what = what['title']
        category.log(CategoryLogRealm.category, LogKind.change, 'Category', f'{what} updated', session.user,
                     data={'Changes': make_diff_log(changes, log_fields)})
    logger.info('Category %s updated by %s', category, session.user)


def update_event_move_request(request, accept, reason=None):
    request.state = MoveRequestState.rejected
    request.state_reason = reason
    request.moderator = session.user
    if accept:
        request.state = MoveRequestState.accepted
        request.state_reason = None
        request.event.move(request.category)
    db.session.flush()
