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

"""
Basic fossils for data export
"""

from indico.util.fossilize import IFossil
from indico.util.fossilize.conversion import Conversion
from MaKaC.webinterface import urlHandlers

class IHTTPAPIResultFossil(IFossil):

    def getTS(self):
        pass
    getTS.name = 'ts'

    def getResults(self):
        pass

class IConferenceMetadataFossil(IFossil):

    def getId(self):
        pass

    def getStartDate(self):
        pass
    getStartDate.convert = Conversion.datetime

    def getEndDate(self):
        pass
    getEndDate.convert = Conversion.datetime

    def getTitle(self):
        pass

    def getDescription(self):
        pass

    def getType(self):
        pass

    def getOwner(self):
        pass
    getOwner.convert = lambda x: x.getTitle()

    def getTimezone(self):
        pass

    def getLocation(self):
        """ Location (CERN/...) """
    getLocation.convert = lambda l: l and l.getName()

    def getLocator(self):
        pass
    getLocator.convert = Conversion.url(urlHandlers.UHConferenceDisplay)
    getLocator.name = 'url'

    def getRoom(self):
        """ Room (inside location) """
    getRoom.convert = lambda r: r and r.getName()
