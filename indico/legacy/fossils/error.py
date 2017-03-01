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
from indico.legacy.webinterface.common.tools import escape_html


class ICausedErrorFossil(IFossil):

    def getMessage(self):
        pass
    getMessage.convert = escape_html

    def getCode(self):
        pass

    def getInner(self):
        pass

    def getType(self):
        pass


class INoReportErrorFossil(ICausedErrorFossil):

    def getTitle(self):
        """
        A title for the error message - will be shown on the client side
        """

    def getExplanation(self):
        """
        Additional error information (can be shown on the client side)
        """
