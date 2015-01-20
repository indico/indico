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


from MaKaC.common.fossilize import IFossil
from MaKaC.common.Conversion import Conversion

class ISubContributionFossil(IFossil):

    def getId(self):
        pass

    def getParent(self):
        pass
    getParent.convert = lambda p: p.getId()
    getParent.name = 'parentId'

    def getTitle(self):
        pass

    def getDuration(self):
        pass
    getDuration.convert = Conversion.duration


class ISubContribParticipationFossil(IFossil):

    def getId(self):
        pass

    def getFullName(self):
        pass


class ISubContribParticipationFullFossil(ISubContribParticipationFossil):

    def getTitle(self):
        pass

    def getFirstName(self):
        pass

    def getFamilyName(self):
        pass

    def getAffiliation(self):
        pass

    def getEmail(self):
        pass

    def getAddress(self):
        pass

    def getPhone(self):
        pass

    def getFax(self):
        pass


class ISubContributionWithSpeakersFossil(ISubContributionFossil):

    def getSpeakerList(self):
        pass
    getSpeakerList.result = ISubContribParticipationFossil
