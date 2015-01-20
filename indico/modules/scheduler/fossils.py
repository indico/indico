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

"""
Fossils for tasks
"""

from indico.util.fossilize import IFossil
from indico.util.fossilize.conversion import Conversion

class ITaskFossil(IFossil):
    """
    A fossil representing a scheduler task
    """
    def getId():
        pass

    def getTypeId():
        pass

    def getStartOn():
        pass
    getStartOn.convert = Conversion.datetime

    def getStartedOn(self):
        pass
    getStartedOn.convert = Conversion.datetime

    def getEndedOn():
        pass
    getEndedOn.convert = Conversion.datetime

    def getCreatedOn():
        pass
    getCreatedOn.convert = Conversion.datetime


class ITaskOccurrenceFossil(IFossil):
    """
    A task occurrence
    """

    def getId():
        pass

    def getStartedOn(self):
        pass
    getStartedOn.convert = Conversion.datetime

    def getEndedOn(self):
        pass
    getEndedOn.convert = Conversion.datetime

    def getTask(self):
        pass
    getTask.result = ITaskFossil
