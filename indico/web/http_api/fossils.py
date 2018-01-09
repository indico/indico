# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

"""
Basic fossils for data export
"""

from indico.util.fossilize import IFossil
from indico.util.fossilize.conversion import Conversion


class IHTTPAPIErrorFossil(IFossil):
    def getMessage(self):
        pass


class IHTTPAPIResultFossil(IFossil):
    def getTS(self):
        pass
    getTS.name = 'ts'

    def getURL(self):
        pass
    getURL.name = 'url'

    def getResults(self):
        pass


class IHTTPAPIExportResultFossil(IHTTPAPIResultFossil):
    def getCount(self):
        pass

    # New SQL-based hooks do not use it anymore, so we deprecate it for everything.
    # def getComplete(self):
    #     pass

    def getAdditionalInfo(self):
        pass


class IPeriodFossil(IFossil):
    def startDT(self):
        pass
    startDT.convert = Conversion.datetime

    def endDT(self):
        pass
    endDT.convert = Conversion.datetime
