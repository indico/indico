# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os

from celery.schedules import crontab

from indico.core.celery import celery
from indico.modules.users import logger
from indico.modules.users.models.users import ProfilePictureSource, User
from indico.modules.users.util import get_gravatar_for_user
from indico.util.fs import secure_filename
from indico.util.string import crc32
from indico.util.struct.iterables import committing_iterator


@celery.periodic_task(name='update_gravatars', run_every=crontab(minute='0', hour='0'))
def update_gravatars():
    users = User.query.filter(~User.is_deleted, User.picture_source == ProfilePictureSource.gravatar).all()
    for user in committing_iterator(users):
        gravatar = get_gravatar_for_user(user, identicon=False)
        new_hash = crc32(gravatar)
        if new_hash == user.picture_metadata['hash']:
            continue
        user.picture = gravatar
        user.picture_metadata = {
            'hash': new_hash,
            'size': len(gravatar),
            'filename': os.path.splitext(secure_filename('gravatar', 'user'))[0] + '.png',
            'content_type': 'image/png'
        }
        logger.info('Gravatar of user %s updated', user)
