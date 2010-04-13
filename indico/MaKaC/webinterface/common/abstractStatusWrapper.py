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
from MaKaC.review import AbstractStatusSubmitted, AbstractStatusAccepted,\
                AbstractStatusRejected, AbstractStatusUnderReview,\
                AbstractStatusProposedToAccept, AbstractStatusProposedToReject,\
                AbstractStatusInConflict,AbstractStatusWithdrawn,\
                AbstractStatusDuplicated,AbstractStatusMerged
from MaKaC.common import Config
from MaKaC.i18n import _
    

class AbstractStatusList:
    """Provides unified captions and colors for the different abstract status.

        Abstract status must be shown in the interface in several places, this
        class centralises the captions, colors and other properties of the 
        different abstract status classes.
    """
    def __init__(self):
        self._statusProps = {"submitted": [ _("submitted"), "white", "as_submitted", _("S")], \
                        "accepted": [ _("accepted"), "white", "as_accepted", _("A")], \
                        "rejected": [ _("rejected"), "white", "as_rejected", _("R")], \
                        "ur": [ _("under review"), "white", "as_review", _("UR")], \
                        "pa":[ _("proposed to accept"),"white","as_prop_accept", _("PA")], \
                        "pr":[ _("proposed to reject"),"white","as_prop_reject", _("PR")],\
                        "conflict":[ _("in conflict"),"white","as_conflict", _("C")], \
                        "withdrawn": [ _("withdrawn"), "white", "as_withdrawn", _("W")], \
                        "duplicated": [ _("duplicated"),"white","as_withdrawn", _("D")],\
                        "merged": [ _("merged"),"white","as_withdrawn", _("M")] } 
                        
        self._statusIds = { AbstractStatusSubmitted: "submitted", \
                            AbstractStatusAccepted: "accepted", \
                            AbstractStatusRejected: "rejected", \
                            AbstractStatusUnderReview: "ur", \
                            AbstractStatusProposedToAccept: "pa", \
                            AbstractStatusProposedToReject: "pr", \
                            AbstractStatusInConflict: "conflict", \
                            AbstractStatusWithdrawn: "withdrawn",\
                            AbstractStatusDuplicated: "duplicated",\
                            AbstractStatusMerged: "merged" }
        
    
    def _getCaption( self, statusId ):
        return self._statusProps.get( statusId,[""] )[0]
    
    def _getCode(self,statusId):
        return self._statusProps.get(statusId,["","","",""])[3]
    
    def _getColor( self, statusId ):
        return self._statusProps.get( statusId, ["",""] )[1]

    def _getIconURL( self, statusId ):
        return Config.getInstance().getSystemIconURL( self._statusProps.get( statusId, ["","",""])[2])
    
    def getId(self, statusClass):
        return self._statusIds.get(statusClass, "")
    
    def getStatus( self, id ):
        for i in self._statusIds.iteritems():
            if i[1] == id:
                return i[0]
        return None

    def getCaption(self, statusClass):
        """Returns the caption for a given abstract status class.
        """
        return self._getCaption( self.getId( statusClass ) )

    def getCode(self,statusClass):
        """
        """
        return self._getCode(self.getId(statusClass))

    def getColor(self, statusClass):
        """Returns the color for a given abstract status.
        """
        return self._getColor( self.getId( statusClass ) )
    
    def getIconURL( self, statusClass ):
        """
        """
        return self._getIconURL( self.getId( statusClass ) )

    def getStatusList(self):
        """Gives a list of all the abstract status.
        """
        return self._statusIds.keys()
