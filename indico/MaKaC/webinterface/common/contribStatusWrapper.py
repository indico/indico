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
"""
from MaKaC.common import Config
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
    

