# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

# legacy imports
from MaKaC.common import DBMgr

# indico imports
from indico.modules.scheduler import PeriodicTask
from indico.util.date_time import nowutc, int_timestamp

# plugin imports
from indico.ext.livesync import SyncManager


class LiveSyncUpdateTask(PeriodicTask):
    """
    A task that periodically checks which sources need to be "pushed"
    """

    def run(self):
        sm = SyncManager.getDBInstance()

        logger = self.getLogger()

        # go over all the agents
        for agtName, agent in sm.getAllAgents().iteritems():

            # skip agents if they're not active
            if not agent.isActive():
                logger.warning("Agent '%s' is not active - skipping" % agtName)
                continue

            logger.info("Starting agent '%s'" % agtName)
            try:
                dbi = DBMgr.getInstance()
                # pass the current time and a logger
                result = agent.run(int_timestamp(nowutc()), logger=logger, dbi=dbi)
            except:
                logger.exception("Problem running agent '%s'" % agtName)
                return

            if result:
                logger.info("Acknowledged successful operation")
                agent.acknowledge()
                dbi.commit()
            else:
                logger.info("'Acknowledge' not done - no records?")
            logger.info("Agent '%s' finished" % agtName)
