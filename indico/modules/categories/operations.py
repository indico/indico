# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.categories import logger
from indico.modules.categories.models.categories import Category
from indico.modules.categories.models.event_move_request import MoveRequestState
from indico.modules.categories.util import format_visibility
from indico.modules.logs.models.entries import CategoryLogRealm, EventLogRealm, LogKind
from indico.modules.logs.util import make_diff_log
from indico.util.signals import make_interceptable
from indico.util.string import crc32


def create_category(parent, data):
    category = Category(parent=parent)
    category.populate_from_dict(data, keys=('title',))
    data.setdefault('default_event_themes', parent.default_event_themes)
    data.setdefault('timezone', parent.timezone)
    db.session.add(category)
    db.session.flush()
    category.populate_from_dict(data)
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


@make_interceptable
def update_category(category, data, *, skip=(), _extra_log_fields=None):
    changes = category.populate_from_dict(data, skip=skip)
    db.session.flush()
    signals.category.updated.send(category)
    logger.info('Category %s updated with %r by %s', category, data, session.user)
    _log_category_update(category, changes, _extra_log_fields)


@make_interceptable
def update_category_protection(category, data, *, _extra_log_fields=None):
    changes = category.populate_from_dict(data)
    db.session.flush()
    signals.category.updated.send(category, changes=changes)
    logger.info('Protection of category %r updated with %r by %r', category, data, session.user)
    if changes:
        log_fields = {'protection_mode': 'Protection mode',
                      'own_no_access_contact': 'No access contact',
                      'visibility': {'title': 'Visibility', 'type': 'string',
                                     'convert': lambda changes: [format_visibility(category, x) for x in changes]},
                      'event_creation_mode': 'Event creation mode',
                      **(_extra_log_fields or {})}
        category.log(CategoryLogRealm.category, LogKind.change, 'Category', 'Protection updated', session.user,
                     data={'Changes': make_diff_log(changes, log_fields)})


def _format_wallet_credentials(credentials):
    if not credentials:
        return '{}'
    keyhash = crc32(credentials.get('private_key') or '')
    return repr({**credentials, 'private_key': f'<hidden:{keyhash}>'})


def _format_secret(secret):
    return f'<hidden:{crc32(secret)}>' if secret else ''


def _log_category_update(category, changes, extra_log_fields):
    extra_fields = {'google_wallet_settings': ('google_wallet_credentials', 'google_wallet_issuer_name',
                                               'google_wallet_issuer_id'),
                    'apple_wallet_settings': ('apple_wallet_certificate', 'apple_wallet_key', 'apple_wallet_password')}
    for extra_field_name, extra_field_keys in extra_fields.items():
        if settings := changes.pop(extra_field_name, None):
            for key in extra_field_keys:
                old = settings[0].get(key)
                new = settings[1].get(key)
                if old != new:
                    changes[key] = (old, new)

    log_fields = {
        'title': {'title': 'Title', 'type': 'string'},
        'description': 'Description',
        'timezone': {'title': 'Timezone', 'type': 'string'},
        'suggestions_disabled': 'Disable suggestions',
        'is_flat_view_enabled': 'Allow flat view',
        'show_future_months': 'Future months threshold',
        'event_message_mode': 'Event header message type',
        'event_message': 'Event header message',
        'notify_managers': 'Notify managers about event creation',
        'event_creation_notification_emails': 'Event creation notification emails',
        'google_wallet_mode': 'Google Wallet mode',
        'google_wallet_issuer_id': {'title': 'Google Wallet Issuer ID', 'type': 'string'},
        'google_wallet_issuer_name': {'title': 'Google Wallet Issuer name', 'type': 'string'},
        'google_wallet_credentials': {
            'title': 'Google Wallet credentials',
            'type': 'text',
            'convert': lambda changes: [_format_wallet_credentials(x) for x in changes],
        },
        'apple_wallet_mode': 'Apple Wallet mode',
        'apple_wallet_certificate': {'title': 'Apple Wallet certificate', 'type': 'text'},
        'apple_wallet_key': {
            'title': 'Apple Wallet private key',
            'type': 'string',
            'convert': lambda changes: [_format_secret(x) for x in changes]
        },
        'apple_wallet_password': {
            'title': 'Apple Wallet passphrase',
            'type': 'string',
            'convert': lambda changes: [_format_secret(x) for x in changes]
        },
        **(extra_log_fields or {})
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


def update_event_move_request(request, accept, reason=''):
    request.state = MoveRequestState.rejected
    request.moderator_comment = reason
    request.moderator = session.user
    log_meta = {'event_move_request_id': request.id}
    if accept:
        request.state = MoveRequestState.accepted
        request.event.move(request.category, log_meta=log_meta)
    else:
        category = request.category
        event = request.event
        sep = ' \N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK} '
        event.log(EventLogRealm.event, LogKind.negative, 'Category', 'Move request rejected', session.user,
                  data={'Category ID': category.id, 'Category': sep.join(category.chain_titles), 'Reason': reason},
                  meta=log_meta)
        category.log(CategoryLogRealm.events, LogKind.negative, 'Moderation', 'Event move rejected', session.user,
                     data={'Event ID': event.id, 'Event title': event.title, 'Reason': reason}, meta=log_meta)

    db.session.flush()
