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
"""
from indico.core.config import Config
from MaKaC.conference import ContribStatusSch,ContribStatusNotSch
from MaKaC.conference import ContribStatusWithdrawn
from MaKaC.i18n import _

class ContribStatusList:
    """
    """

    _statusProps = {"ns":[ "not scheduled","", "NS"], \
                        "s":[ "scheduled","", "S"], \
                        "withdrawn":[ "withdrawn","", "W"] }

    _statusIds = { ContribStatusSch: "s", \
                            ContribStatusNotSch: "ns", \
                            ContribStatusWithdrawn: "withdrawn" }

    @classmethod
    def _getCaption( cls, statusId ):
        return _(cls._statusProps.get(statusId,[""])[0])

    @classmethod
    def _getCode(cls,statusId):
        return _(cls._statusProps.get(statusId,["","",""])[2])

    @classmethod
    def _getIconURL(cls,statusId):
        return Config.getInstance().getSystemIconURL(cls._statusProps.get(statusId,["","",""])[1])

    @classmethod
    def getId(cls,statusClass):
        return cls._statusIds.get(statusClass, "")

    @classmethod
    def getStatus(cls,id):
        for i in cls._statusIds.iteritems():
            if i[1] == id:
                return i[0]
        return None

    @classmethod
    def getCaption(cls,statusClass):
        """Returns the caption for a given abstract status class.
        """
        return cls._getCaption(cls.getId(statusClass))

    @classmethod
    def getCode(cls,statusClass):
        """
        """
        return cls._getCode(cls.getId(statusClass))

    @classmethod
    def getIconURL(cls,statusClass):
        """
        """
        return cls._getIconURL(cls.getId(statusClass))

    @classmethod
    def getList(cls):
        """Gives a list of all the abstract status.
        """
        return cls._statusIds.keys()


