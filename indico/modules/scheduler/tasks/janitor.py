# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from datetime import timedelta

from indico.core.db import DBMgr
from indico.core.config import Config
from indico.util.date_time import now_utc
from indico.modules import ModuleHolder
from indico.modules.scheduler.tasks.periodic import PeriodicTask

from MaKaC.conference import CategoryManager
from MaKaC.common.timezoneUtils import nowutc


MAX_OFFLINE_WEBPAGE_LIFE = 30 * 24 * 3600


def delete_offline_events(dbi, logger):
    logger.info("Checking which offline events should be deleted")
    offline_events_module = ModuleHolder().getById("offlineEvents")
    events = offline_events_module.getOfflineEventIndex()
    for conf_requests in events.itervalues():
        for req in conf_requests:
            if req.status == "Generated" and req.creationTime and \
               nowutc() - req.creationTime > timedelta(seconds=MAX_OFFLINE_WEBPAGE_LIFE):
                logger.info("Deleting offline req {0}".format(req.id))
                offline_events_module.removeOfflineFile(req)
                logger.info("Deleted offline req {0}".format(req.id))


def cleanup_categories(dbi, logger):
    config = Config.getInstance()

    logger.info("Checking whether any categories should be cleaned up")

    for categ_id, days in config.getCategoryCleanup().items():
        try:
            category = CategoryManager().getById(categ_id)
        except KeyError:
            logger.warning("Category '{0}' does not exist!".format(categ_id))
            continue

        now = now_utc()

        to_delete = [ev for ev in category.conferences if (now - ev._creationDS) > timedelta(days=days)]

        if to_delete:
            logger.info("Category '{0}': {1} events were created more than {2} days ago and will be deleted".format(
                categ_id, len(to_delete), days
            ))

            for i, event in enumerate(to_delete, 1):
                logger.info("Deleting {0}".format(repr(event)))
                event.delete()
                if i % 100 == 0:
                    dbi.commit()
            dbi.commit()


class JanitorTask(PeriodicTask):
    def run(self):
        dbi = DBMgr.getInstance()
        logger = self.getLogger()

        delete_offline_events(dbi, logger)
        cleanup_categories(dbi, logger)
