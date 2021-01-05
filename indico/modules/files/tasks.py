# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import timedelta

from celery.schedules import crontab
from sqlalchemy.orm.attributes import flag_modified

from indico.core.celery import celery
from indico.core.config import config
from indico.core.db import db
from indico.core.storage import StorageError, StorageReadOnlyError
from indico.modules.files import logger
from indico.modules.files.models.files import File
from indico.util.date_time import now_utc


@celery.periodic_task(name='delete_unclaimed_files', run_every=crontab(minute='0', hour='6'))
def delete_unclaimed_files():
    unclaimed_files = (File.query
                       .filter(~File.claimed,
                               File.created_dt <= (now_utc() - timedelta(days=1)),
                               # skip files where deleting failed in the past
                               ~File.meta.op('?')('deletion_failed'))
                       .all())

    for file in unclaimed_files:
        file_repr = repr(file)
        if config.DEBUG:
            logger.info('Would have removed unclaimed file %s (skipped due to debug mode)', file_repr)
            continue
        try:
            file.delete(delete_from_db=True)
        except StorageReadOnlyError:
            file.meta['deletion_failed'] = True
            flag_modified(file, 'meta')
            logger.warn('Could not delete unclaimed file %s (read-only storage)', file_repr)
        except StorageError as exc:
            logger.error('Could not delete unclaimed file %s: %s', file_repr, exc)
        else:
            logger.info('Removed unclaimed file %s', file_repr)
        db.session.commit()
