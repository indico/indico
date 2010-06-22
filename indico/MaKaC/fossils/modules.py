# -*- coding: utf-8 -*-
##
## $Id: modules.py,v 1.00 2010/06/22 15:21:49 irolewic Exp $
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
from MaKaC.fossils.conference import ICategoryFossil, IConferenceMinimalFossil

class INewsItemFossil(IFossil):

    def getId(self):
        pass

    def getAdjustedCreationDate(self):
        pass
    getAdjustedCreationDate.convert = Conversion.datetime
    getAdjustedCreationDate.name = "creationDate"

    def getContent(self):
        pass
    getContent.name = "text"

    def getTitle(self):
        pass

    def getType(self):
        pass

    def getHumanReadableType(self):
        pass

class IObservedObjectFossil(IFossil):

    def getObject(self):
        """ Encapsulated Object - either Category or Conference """
    getObject.result = {"MaKaC.conference.Category": ICategoryFossil,
                        "MaKaC.conference.Conference": IConferenceMinimalFossil}

    def getWeight(self):
        """ Weight of the Observed Object """

    def getAdvertisingDelta(self):
        """ Time delta """
    getAdvertisingDelta.convert = lambda s: s.days
    getAdvertisingDelta.name = "delta"
