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

import recovery
from MaKaC.common import DBMgr
from MaKaC import conference
from datetime import datetime

eventId = "5705"
date = datetime(2006,10,4,23,0)

ch=conference.ConferenceHolder()
dbm=DBMgr.getInstance()
dbm.startRequest()
c=ch.getById(eventId)
cr=recovery.ParticipantRecovery(c)
cr.proceed(date)
