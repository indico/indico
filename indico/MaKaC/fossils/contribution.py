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

from MaKaC.common.fossilize import IFossil
from MaKaC.common.Conversion import Conversion
from MaKaC.fossils.subcontribution import ISubContributionFossil

class IContributionFossil(IFossil):
    
    def getId(self):
        pass
    
    def getTitle(self):
        pass
    
    def getLocation(self):
        pass
    getLocation.convert = lambda l: l and l.getName()
    
    def getRoom(self):
        pass
    getRoom.convert = lambda r: r and r.getName()

    def getStartDate(self):
        pass
    getStartDate.convert = Conversion.datetime
    
    def getEndDate(self):
        pass
    getEndDate.convert = Conversion.datetime
    
    def getDuration(self):
        pass
    getDuration.convert = Conversion.duration

class IContributionParticipationFossil(IFossil):
    
    def getId(self):
        pass
    
    def getFullName(self):
        pass

class IContributionWithSpeakersFossil(IContributionFossil):
    
    def getSpeakerList(self):
        pass
    getSpeakerList.result = IContributionParticipationFossil
    
class IContributionWithSubContribsFossil(IContributionFossil):
    
    def getSubContributionList(self):
        pass
    getSubContributionList.result = ISubContributionFossil