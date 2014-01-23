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

import MaKaC.conference

def prettyPrint(obj):
    if type(obj) == MaKaC.conference.DeletedObject:
        return "DeletedObject<%s>" % (obj.getId())
    elif type(obj) == MaKaC.conference.Conference:
        try:
            owner = obj.getOwner().id
        except:
            owner = 'ORPHAN'

        return "Conference< %s @ %s >" % (obj.getId(),owner)
    elif type(obj) == MaKaC.conference.Contribution:
        try:
            owner = obj.getConference().getId()
        except:
            owner = "ORPHAN"

        return "Contribution< %s @ %s >" % (obj.getId(),owner)
    elif type(obj) == MaKaC.conference.AcceptedContribution:
        try:
            owner = obj.getConference().getId()
        except:
            owner = "ORPHAN"

        return "AcceptedContribution< %s @ %s >" % (obj.getId(),owner)
    elif type(obj) == MaKaC.conference.SubContribution:
        try:
            owner = obj.getOwner().getId()
            conf = obj.getConference().getId()
        except:
            owner = "ORPHAN"
            conf = "ORPHAN"
        return "SubContribution< %s @ %s @ %s >" % (obj.getId(),owner,conf)
    else:
        return obj

def getParent(obj):
    if type(obj) == MaKaC.conference.Conference:
        try:
            return obj.getOwner()
        except:
            return None
    else:
        try:
            return obj.getConference()
        except:
            return None
