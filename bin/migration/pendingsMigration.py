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

from MaKaC.common import DBMgr
from MaKaC.common.pendingQueues import PendingSubmittersHolder, PendingManagersHolder, PendingConfManagersHolder,PendingCoordinatorsHolder









DBMgr.getInstance().startRequest()
phs = PendingSubmittersHolder()
for pends in phs._idx.dump().values():
    for pend in pends:
        contrib=pend.getContribution()
        if contrib and contrib.getConference():
            contrib.grantSubmission(pend, sendEmail=False)
            pend.getConference().getPendingQueuesMgr().removePendingSubmitter(pend)
DBMgr.getInstance().endRequest()

DBMgr.getInstance().startRequest()
pmh = PendingManagersHolder()
for pends in pmh._idx.dump().values():
    for pend in pends:
        session=pend.getSession()
        if session and session.getConference():
            session.grantModification(pend, sendEmail=False)
            pend.getConference().getPendingQueuesMgr().removePendingManager(pend)
DBMgr.getInstance().endRequest()

DBMgr.getInstance().startRequest()
pcmh = PendingConfManagersHolder()
for pends in pcmh._idx.dump().values():
    for pend in pends:
        conf=pend.getConference()
        if conf:
            conf.grantModification(pend, sendEmail=False)
            pend.getConference().getPendingQueuesMgr().removePendingManager(pend)
DBMgr.getInstance().endRequest()

DBMgr.getInstance().startRequest()
pch = PendingCoordinatorsHolder()
for pends in pch._idx.dump().values():
    for pend in pends:
        session=pend.getSession()
        if session and session.getConference():
            session.addCoordinator(pend, sendEmail=False)
            pend.getConference().getPendingQueuesMgr().removePendingCoordinator(pend)
DBMgr.getInstance().endRequest()



