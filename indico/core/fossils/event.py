# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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


from indico.legacy.common.fossilize import IFossil


class IErrorReportFossil(IFossil):
    def getMessage(self):
        pass

    def getCode(self):
        """
        Compatibility to json-rpc errors
        """
    getCode.produce = lambda self: ""

    def getInner(self):
        """
        Compatibility to json-rpc errors
        """
    getInner.produce = lambda self: None

    def getType(self):
        """
        Compatibility to json-rpc errors
        """
    getType.produce = lambda self: None


class IErrorNoReportFossil(IErrorReportFossil):

    def getType(self):
        """
        Compatibility to json-rpc errors
        """
    getType.produce = lambda self: "noReport"

    def getExplanation(self):
        pass
