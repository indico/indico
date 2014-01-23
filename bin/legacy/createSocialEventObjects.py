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
from MaKaC import conference
from MaKaC.registration import SocialEvent

def copy(l):
    nl = []
    for e in l:
        nl.append(e)
    return nl

DBMgr.getInstance().startRequest()
error = False
ch = conference.ConferenceHolder()
for conf in ch.getList():
    for reg in conf.getRegistrantsList():
        l = []
        for seItem in reg.getSocialEvents():
            newSE = SocialEvent(seItem)
            l.append(newSE)
        reg.setSocialEvents(l)

if not error:
    DBMgr.getInstance().endRequest()
    print "No error. The change are saved"
else:
    print "There were errors. The changes was not saved"

