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

import sys
sys.path.append("c:/development/indico/code/code")
from indico.core.db import DBMgr
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
