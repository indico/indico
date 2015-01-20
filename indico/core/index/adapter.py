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

from zope.interface import Interface


class IIndexableByStartDateTime(Interface):

    def getAdjustedStartDate(self):
        """
        Returns a tz-aware datetime
        """


class IIndexableByEndDateTime(Interface):

    def getAdjustedEndDate(self):
        """
        Returns a tz-aware datetime
        """


class IIndexableByArbitraryDateTime(Interface):

    def getIndexingDateTime():
        """
        Return an arbitrary tz-aware datetime (class will decide what)
        """


class IIndexableById(Interface):

    def getId():
        """
        Return the id of the object
        """
