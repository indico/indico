# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from celery.schedules import crontab
from sqlalchemy.orm.attributes import flag_modified

from indico.core.celery import celery
from indico.modules.users import logger
from indico.modules.users.models.users import ProfilePictureSource, User
from indico.modules.users.util import get_gravatar_for_user, set_user_avatar
from indico.util.string import crc32
from indico.util.struct.iterables import committing_iterator


@celery.periodic_task(name='update_gravatars', run_every=crontab(minute='0', hour='0'))
def update_gravatars(user=None):
    if user is not None:
        # explicitly scheduled update (after an email change)
        if user.picture_source not in (ProfilePictureSource.gravatar, ProfilePictureSource.identicon):
            return
        users = [user]
    else:
        users = User.query.filter(~User.is_deleted, User.picture_source == ProfilePictureSource.gravatar).all()
    for user in committing_iterator(users):
        gravatar, lastmod = get_gravatar_for_user(user, identicon=False, lastmod=user.picture_metadata['lastmod'])
        if gravatar is None:
            logger.debug('Gravatar for %r did not change (not modified)', user)
            continue
        if crc32(gravatar) == user.picture_metadata['hash']:
            logger.debug('Gravatar for %r did not change (same hash)', user)
            user.picture_metadata['lastmod'] = lastmod
            flag_modified(user, 'picture_metadata')
            continue
        set_user_avatar(user, gravatar, 'gravatar', lastmod)
        logger.info('Gravatar of user %s updated', user)
