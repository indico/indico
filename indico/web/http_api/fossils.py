# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
