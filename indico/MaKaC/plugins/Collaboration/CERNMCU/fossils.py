# -*- coding: utf-8 -*-
##
## $Id: common.py,v 1.4 2009/04/25 17:27:00 dmartinc Exp $
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

from MaKaC.common.fossilize import IFossil

class IParticipantFossil(IFossil):

    def getType(self):
        pass

    def getId(self):
        pass
    getId.name = "participantId"

    def getParticipantName(self):
        pass

    def getDisplayName(self):
        pass

    def getIp(self):
        pass

    def getParticipantType(self):
        pass

    def getParticipantProtocol(self):
        pass

    def getCallState(self):
        pass

class IParticipantPersonFossil(IParticipantFossil):

    def getTitle(self):
        pass

    def getFamilyName(self):
        pass

    def getFirstName(self):
        pass

    def getAffiliation(self):
        pass


class IParticipantRoomFossil(IParticipantFossil):

    def getName(self):
        pass

    def getInstitution(self):
        pass


class IRoomWithH323Fossil(IFossil):

    def getLocation(self):
        pass
    getLocation.name = "institution"

    def getName(self):
        pass

    def getIp(self):
        pass
