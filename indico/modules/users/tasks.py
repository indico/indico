# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from celery.schedules import crontab
from sqlalchemy.orm.attributes import flag_modified

from indico.core.celery import celery
from indico.core.db import db
from indico.modules.users import logger
from indico.modules.users.export import export_user_data as _export_user_data
from indico.modules.users.export import get_old_requests
from indico.modules.users.models.export import DataExportRequestState
from indico.modules.users.models.users import ProfilePictureSource, User
from indico.modules.users.util import get_gravatar_for_user, set_user_avatar
from indico.util.iterables import committing_iterator
from indico.util.string import crc32


@celery.periodic_task(name='update_gravatars', run_every=crontab(minute='0', hour='0'))
def update_gravatars(user=None):
    if user is not None:
        # explicitly scheduled update (after an email change)
        if user.picture_source not in (ProfilePictureSource.gravatar, ProfilePictureSource.identicon):
            return
        users = [user]
    else:
        users = User.query.filter(~User.is_deleted, User.picture_source == ProfilePictureSource.gravatar).all()
    for u in committing_iterator(users):
        _do_update_gravatar(u)


def _do_update_gravatar(user):
    gravatar, lastmod = get_gravatar_for_user(user, identicon=False, lastmod=user.picture_metadata['lastmod'])
    if gravatar is None:
        logger.debug('Gravatar for %r did not change (not modified)', user)
        return
    if crc32(gravatar) == user.picture_metadata['hash']:
        logger.debug('Gravatar for %r did not change (same hash)', user)
        user.picture_metadata['lastmod'] = lastmod
        flag_modified(user, 'picture_metadata')
        return
    set_user_avatar(user, gravatar, 'gravatar', lastmod)
    logger.info('Gravatar of user %s updated', user)


@celery.task(name='export_user_data')
def export_user_data(user, options, include_files):
    _export_user_data(user, options, include_files)


@celery.periodic_task(name='user_data_export_cleanup', run_every=crontab(hour='4', day_of_week='monday'))
def user_data_export_cleanup(days=30):
    """Clean up old user data exports.

    Files belonging to old data exports are marked for deletion
    by setting `claimed=False`. The files will then be automatically
    deleted by the daily `delete_unclaimed_files` task.

    :param days: minimum age of the data export to be marked for removal
    """
    old_requests = get_old_requests(days)

    logger.info('Marking for deletion %d expired user data exports from the past %d days', len(old_requests), days)
    for request in old_requests:
        request.state = DataExportRequestState.expired
        if request.file:
            request.file.claimed = False
    db.session.commit()
