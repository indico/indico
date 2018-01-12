# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

"""
This module contains very generic Celery tasks which are not specific
to any other module.  Please add tasks in here only if they are generic
enough to be possibly useful somewhere else.  If you need to import
anything from `indico.modules`, your task most likely does not belong
in here but in your module instead.
"""

from __future__ import unicode_literals

from datetime import timedelta

from celery.schedules import crontab

from indico.core.celery import celery
from indico.util.fs import cleanup_dir


def _log_deleted(logger, msg, files):
    for name in sorted(files):
        logger.info(msg, name)


@celery.periodic_task(name='temp_cleanup', run_every=crontab(minute='0', hour='4'))
def temp_cleanup():
    """Cleanup temp/cache dirs"""
    from indico.core.config import config
    from indico.core.logger import Logger
    logger = Logger.get()
    deleted = cleanup_dir(config.CACHE_DIR, timedelta(days=1),
                          exclude=lambda x: x.startswith('webassets-'))
    _log_deleted(logger, 'Deleted from cache: %s', deleted)
    deleted = cleanup_dir(config.TEMP_DIR, timedelta(days=1))
    _log_deleted(logger, 'Deleted from temp: %s', deleted)
