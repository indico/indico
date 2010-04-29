# -*- coding: utf-8 -*-
##
## $Id: options.py,v 1.1 2009/04/09 13:13:18 dmartinc Exp $
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

from MaKaC.services.implementation.collaboration import CollaborationPluginServiceBase,\
    CollaborationPluginServiceBookingModifBase
from MaKaC.plugins.Collaboration.CERNMCU.common import CERNMCUException, CERNMCUError
from MaKaC.i18n import _
from MaKaC.common.fossilize import fossilize
from MaKaC.plugins.Collaboration.fossils import ICSBookingBaseConfModifFossil

class ParticipantServiceBase(CollaborationPluginServiceBookingModifBase):

    def __init__(self, params, aw):
        CollaborationPluginServiceBase.__init__(self, params, aw)
        self._participant = None

    def _checkParams(self):
        CollaborationPluginServiceBookingModifBase._checkParams(self)
        participantId = self._params.get("participantId", None)
        if participantId:
            self._participant = self._booking.getParticipantById(participantId)
        else:
            raise CERNMCUException( _("Service ") + str(self.__class__.__name__) + _(" called without a participantId parameter"))


class ConnectParticipantService(ParticipantServiceBase):

    def _getAnswer(self):
        result = self._booking.startSingleParticipant(self._participant)
        if isinstance(result, CERNMCUError):
            return fossilize(result)
        else:
            return fossilize(self._booking, ICSBookingBaseConfModifFossil, tz = self._conf.getTimezone())



class DisconnectParticipantService(ParticipantServiceBase):

    def _getAnswer(self):
        result = self._booking.stopSingleParticipant(self._participant)
        if isinstance(result, CERNMCUError):
            return fossilize(result)
        else:
            return fossilize(self._booking, ICSBookingBaseConfModifFossil, tz = self._conf.getTimezone())
