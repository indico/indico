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

from indico.core.db import DBMgr
from MaKaC.conference import ConferenceHolder

CONFID='XXXXX'  # Replace XXXX with the ID of your conference.

DBMgr.getInstance().startRequest()

c=ConferenceHolder().getById(CONFID)

for contrib in c.getContributionList():
    contrib._submittersEmail=map(lambda x: x.lower(),contrib.getSubmitterEmailList())

DBMgr.getInstance().commit()
DBMgr.getInstance().sync()

for contrib in c.getContributionList():
    for email in contrib.getSubmitterEmailList():
        email=email.lower()
        res=AvatarHolder().match({'email':email})
        if len(res)==1:
            contrib.grantSubmission(res[0])
            contrib.revokeSubmissionEmail(email)

DBMgr.getInstance().commit()

DBMgr.getInstance().endRequest()

