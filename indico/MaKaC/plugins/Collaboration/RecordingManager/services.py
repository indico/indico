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
from MaKaC.plugins.Collaboration.RecordingManager.exceptions import RecordingManagerException
from MaKaC.plugins.Collaboration.RecordingManager.common import createIndicoLink, createCDSRecord
from MaKaC.plugins.Collaboration.RecordingManager.micala import MicalaCommunication

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
        MicalaCommunication.updateMicala(self._params.get('IndicoID', None), self._params.get('LOID', None))
        return {'some':'thing'}

class RMCreateCDSRecordService(CollaborationPluginServiceBase):

    def _checkParams(self):
        CollaborationPluginServiceBase._checkParams(self) #puts the Conference in self._conf
        self._IndicoID    = self._params.get('IndicoID',    None)
        self._LOID        = self._params.get('LOID',        None)
        self._confId      = self._params.get('conference',  None)
        self._videoFormat = self._params.get('videoFormat', None)
        self._contentType = self._params.get('contentType', None)
        self._languages   = self._params.get('languages',   None)

        if not self._contentType:
            raise RecordingManagerException("No content type supplied (plain video or web lecture)")
        if not self._IndicoID:
            raise RecordingManagerException("No IndicoID supplied")

        if self._contentType == 'web_lecture':
            if not self._LOID:
                raise RecordingManagerException("No LOID supplied")
        elif self._contentType == 'plain_video':
            if not self._videoFormat:
                raise RecordingManagerException("No video format supplied")

        if not self._confId:
            raise RecordingManagerException("No conference ID supplied")

        if not self._languages:
            raise RecordingManagerException("No languages supplied")

    def _getAnswer(self):
        # Update the micala database
        resultUpdateMicala = MicalaCommunication.updateMicala(self._IndicoID,
                                          self._contentType,
                                          self._params.get('LOID', None))

        # Get the MARC XML and submit it to CDS
        resultCreateCDSRecord = createCDSRecord(self._aw,
                                                self._IndicoID,
                                                self._contentType,
                                                self._videoFormat,
                                                self._languages)

#        raise RecordingManagerException("got this far")

        return str(resultUpdateMicala) + ', ' + str(resultCreateCDSRecord)

class RMCreateIndicoLinkService(CollaborationPluginServiceBase):

    def _checkParams(self):
        CollaborationPluginServiceBase._checkParams(self) #puts the Conference in self._conf
        self._IndicoID = self._params.get('IndicoID',   None)
        self._LOID     = self._params.get('LOID',       None)
        self._confId   = self._params.get('conference', None)
        self._CDSID    = self._params.get('CDSID',      None)

        if not self._IndicoID:
            raise RecordingManagerException("No IndicoID supplied")
        if not self._confId:
            raise RecordingManagerException("No conference ID supplied")
        if not self._CDSID:
            raise RecordingManagerException("No CDS record ID supplied")

    def _getAnswer(self):
        # Create the Indico link
        resultCreateIndicoLink = createIndicoLink(self._IndicoID, self._CDSID)

        return str(resultCreateIndicoLink)

# In case we want to update list of orphans after page has loaded...
class RMOrphansService(CollaborationPluginServiceBase):

    def _getAnswer(self):
        pass
        #orphans = getOrphans()
