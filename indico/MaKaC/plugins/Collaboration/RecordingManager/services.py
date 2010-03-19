# -*- coding: utf-8 -*-
##
## $Id: services.py,v 1.1 2009/04/09 13:13:18 dmartinc Exp $
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

from MaKaC.services.implementation.collaboration import CollaborationPluginServiceBase
from MaKaC.plugins.Collaboration.RecordingRequest.common import getTalks
from MaKaC.plugins.Collaboration.RecordingManager.common import RecordingManagerException,\
    updateMicala, createCDSRecord


class RMLinkService(CollaborationPluginServiceBase):

    def _checkParams(self):
        CollaborationPluginServiceBase._checkParams(self) #puts the Conference in self._conf
        self._IndicoID = self._params.get('IndicoID', None)
        self._LOID     = self._params.get('LOID', None)

        if not self._IndicoID:
            raise RecordingManagerException("No IndicoID supplied")
        if not self._LOID:
            raise RecordingManagerException("No LOID supplied")

    def _getAnswer(self):
#        here is where we make a submission to the database?
        updateMicala(self._params.get('IndicoID', None), self._params.get('LOID', None))
        return {'some':'thing'}

class RMCreateCDSRecordService(CollaborationPluginServiceBase):

    def _checkParams(self):
        CollaborationPluginServiceBase._checkParams(self) #puts the Conference in self._conf
        self._IndicoID = self._params.get('IndicoID', None)
        self._LOID     = self._params.get('LOID', None)
        self._confId   = self._params.get('conference', None)

        if not self._IndicoID:
            raise RecordingManagerException("No IndicoID supplied")
        if not self._LOID:
            raise RecordingManagerException("No LOID supplied")
        if not self._confId:
            raise RecordingManagerException("No conference ID supplied")

    def _getAnswer(self):
        # Update the micala database
        resultUpdateMicala = updateMicala(self._IndicoID, self._params.get('LOID', None))

        # Get the MARC XML and submit it to CDS
        resultCreateCDSRecord = createCDSRecord(self._IndicoID, self._aw)

#        raise RecordingManagerException("got this far")

        return str(resultUpdateMicala) + ', ' + str(resultCreateCDSRecord)

class RMCreateIndicoLinkService(CollaborationPluginServiceBase):

    def _checkParams(self):
        CollaborationPluginServiceBase._checkParams(self) #puts the Conference in self._conf
        self._IndicoID = self._params.get('IndicoID', None)
        self._LOID     = self._params.get('LOID', None)
        self._confId   = self._params.get('conference', None)

        if not self._IndicoID:
            raise RecordingManagerException("No IndicoID supplied")
        if not self._LOID:
            raise RecordingManagerException("No LOID supplied")
        if not self._confId:
            raise RecordingManagerException("No conference ID supplied")

    def _getAnswer(self):
        # Create the Indico link
        resultCreateIndicoLink = createIndicoLink(self._IndicoID)

        return str(resultCreateIndicoLink)

# In case we want to update list of orphans after page has loaded...
class RMOrphansService():

    def _getAnswer(self):
        pass
        #orphans = getOrphans()
