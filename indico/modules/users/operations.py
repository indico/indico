# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core import signals
from indico.core.config import config
from indico.core.db import db
from indico.modules.users import User


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
    db.session.flush()
    return user
