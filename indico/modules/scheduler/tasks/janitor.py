# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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
from MaKaC.webinterface.session.sessionManagement import getSessionManager
from indico.modules.scheduler.tasks import PeriodicTask


MAX_SESSION_LIFE = 24 * 3600


def delete_web_sessions(dbi, logger):
    count = 0
    to_delete = []
    batchsize = 1000

    sm = getSessionManager()

    logger.info("Checking which websessions should be deleted")

    for key, session in sm.iteritems():
        count += 1
        if session.get_creation_age() > MAX_SESSION_LIFE:
            to_delete.append(key)

    logger.info("Deleting {0}/{1} websessions".format(len(to_delete), count))

    done = 0

    for key in to_delete:
        sm.delete_session(key)
        done += 1

        if done % 100 == 0:
            dbi.commit()

    logger.info("Deleted {0}/{1} sessions".format(done, len(to_delete)))


class JanitorTask(PeriodicTask):
    def run(self):
        dbi = DBMgr.getInstance()
        delete_web_sessions(dbi, self.getLogger())
