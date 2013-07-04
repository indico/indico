# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

from MaKaC.common import DBMgr
from indico.modules import ModuleHolder
from MaKaC.common.timezoneUtils import nowutc
from indico.modules.scheduler.tasks import PeriodicTask
from datetime import timedelta


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


class JanitorTask(PeriodicTask):
    def run(self):
        dbi = DBMgr.getInstance()
        delete_offline_events(dbi, self.getLogger())
