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

import sys
sys.path.append("c:/development/indico/code/code")
from MaKaC.common import DBMgr
DBMgr.getInstance().startRequest()
from MaKaC.conference import ConferenceHolder,Contribution
from MaKaC.conference import ContributionParticipation
from MaKaC.schedule import LinkedTimeSchEntry
c=ConferenceHolder().getById("2")
sch=[]
for entry in c.getSchedule().getEntries():
    sch.append(entry)
    if isinstance(entry,LinkedTimeSchEntry) and \
            isinstance(entry.getOwner(),Contribution):
        for spk in entry.getOwner().speakers:
            p=ContributionParticipation()
            p.setFirstName(spk.getName())
            p.setFamilyName(spk.getSurName())
            p.setTitle(spk.getTitle())
            p.setEmail(spk.getEmail())
            p.setAffiliation(spk.getOrganisation())
            p.setAffiliation(spk.getOrganisation())
            entry.getOwner().addPrimaryAuthor(p)
            entry.getOwner().addSpeaker(p)
        entry.getOwner().speakers=None
c._setSchedule()
for entry in sch:
    c.getSchedule().addEntry(entry)
c=ConferenceHolder().getById("1")
while len(c.getContributionList())>0:
    c.removeContribution(c.getContributionList()[0])
DBMgr.getInstance().endRequest()
