# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import has_request_context, request, session
from sqlalchemy.exc import IntegrityError

from indico.core.auth import multipass
from indico.core.config import config
from indico.core.db import db
from indico.modules.logs.models.entries import LogKind, UserLogRealm
from indico.modules.users import User, logger, signals
from indico.modules.users.models.emails import UserEmail
from indico.modules.users.util import anonymize_user, merge_users


def create_user(email, data, identity=None, settings=None, other_emails=None, from_moderation=True):
    """Create a new user.

    This may also convert a pending user to a proper user in case the
    email address matches such a user.

    :param email: The primary email address of the user.
    :param data: The data used to populate the user.
    :param identity: An `Identity` to associate with the user.
    :param settings: A dict containing user settings.
    :param other_emails: A set of email addresses that are also used
                         to check for a pending user. They will also
                         be added as secondary emails to the user.
    :param from_moderation: Whether the user was created through the
                            moderation process or manually by an admin.
    """
    if other_emails is None:
        other_emails = set()
    if settings is None:
        settings = {}
    settings.setdefault('timezone', config.DEFAULT_TIMEZONE)
    settings.setdefault('lang', config.DEFAULT_LOCALE)
    settings.setdefault('suggest_categories', False)
    # Get a pending user if there is one
    user = User.query.filter(~User.is_deleted, User.is_pending,
                             User.all_emails.in_({email} | set(other_emails))).first()
    if not user:
        user = User()

    if email in user.secondary_emails:
        # This can happen if there's a pending user who has a secondary email
        # for some weird reason which should now become the primary email...
        user.make_email_primary(email)
    else:
        user.email = email
    user.populate_from_dict(data, skip={'synced_fields'})
    user.is_pending = False
    user.secondary_emails |= other_emails
    user.favorite_users.add(user)
    if identity is not None:
        user.identities.add(identity)
    db.session.add(user)
    db.session.flush()
    user.populate_from_dict(data, keys={'synced_fields'})  # this is a setting, so the user must have an ID
    user.settings.set_multi(settings)
    db.session.flush()
    signals.users.registered.send(user, from_moderation=from_moderation, identity=identity)
    data = {'Moderated': from_moderation}
    if identity:
        data |= {'Provider': multipass.identity_providers[identity.provider].title,
                 'Identifier': identity.identifier}
    if has_request_context():
        data['IP'] = request.remote_addr
    user.log(UserLogRealm.user, LogKind.positive, 'User', 'User created', session.user if session else None, data=data)
    db.session.flush()
    return user


def add_secondary_email(user, email, actor, merge_pending=True):
    """
    Adds a secondary email to a user, optionally merging a pending user with the same email.

    If a pending user exists with the given email, merges that user into the target user
    before adding the email. Logs the action and emits the email_added signal.

    :param user: The target `User` to add the secondary email to.
    :param email: The email address to add as a secondary email.
    :param actor: The `User` performing the action (for logging).
    :param merge_pending: Whether to merge a pending user with the same email (default: True).
    """
    existing = UserEmail.query.filter_by(is_user_deleted=False, email=email).first()
    if merge_pending and existing and existing.user.is_pending:
        logger.info('Found pending user %s to be merged into %s', existing.user, user)
        existing.user.first_name = existing.user.first_name or user.first_name
        existing.user.last_name = existing.user.last_name or user.last_name
        merge_users(existing.user, user)
        existing.user.is_pending = False

    user.secondary_emails.add(email)
    user.log(UserLogRealm.user, LogKind.positive, 'Profile', 'Secondary email added', actor, data={'Email': email})
    signals.users.email_added.send(user, email=email, silent=False)


def delete_or_anonymize_user(user):
    """Delete or anonymize a user.

    Deletes the user, and all their associated data. If it is not possible to delete the user, it will
    instead fallback to anonymizing the user.
    """
    user_repr = repr(user)
    signals.users.db_deleted.send(user, flushed=False)
    try:
        db.session.delete(user)
        db.session.flush()
    except IntegrityError as exc:
        db.session.rollback()
        logger.info('User %r could not be deleted %s', user, str(exc))
        anonymize_user(user)
        logger.info('User %r anonymized %s', session.user if session else None, user_repr)
    else:
        signals.users.db_deleted.send(user, flushed=True)
        logger.info('User %r deleted %s', session.user if session else None, user_repr)
