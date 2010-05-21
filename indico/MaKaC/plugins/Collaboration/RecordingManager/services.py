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
from MaKaC.plugins.Collaboration.RecordingManager.common import createIndicoLink, createCDSRecord, submitMicalaMetadata
from MaKaC.plugins.Collaboration.RecordingManager.micala import MicalaCommunication

class RMCreateCDSRecordService(CollaborationPluginServiceBase):

    def _checkParams(self):
        CollaborationPluginServiceBase._checkParams(self) #puts the Conference in self._conf
        self._IndicoID    = self._params.get('IndicoID',    None)
        self._LOID        = self._params.get('LOID',        None)
        self._LODBID      = self._params.get('LODBID',      None)
        self._confId      = self._params.get('conference',  None)
        self._videoFormat = self._params.get('videoFormat', None)
        self._contentType = self._params.get('contentType', None)
        self._languages   = self._params.get('languages',   None)

        if not self._contentType:
            raise RecordingManagerException("No content type supplied (plain video or web lecture)")
        if not self._IndicoID:
            raise RecordingManagerException("No IndicoID supplied")

        if self._contentType == 'web_lecture':
            if not self._LODBID:
                raise RecordingManagerException("No LODBID supplied")
        elif self._contentType == 'plain_video':
            if not self._videoFormat:
                raise RecordingManagerException("No video format supplied")

        if not self._confId:
            raise RecordingManagerException("No conference ID supplied")

        if not self._languages:
            raise RecordingManagerException("No languages supplied")

    def _getAnswer(self):
        """This method does everything necessary to create a CDS record and also update the micala database.
        For plain_video talks, it does the following:
         - calls createCDSRecord(),
                 which generates the MARC XML,
                 submits it to CDS,
                 and makes sure a record for this talk exists in micala DB
        For web_lecture talks, it does the following:
         - calls createCDSRecord(),
                 which generates the MARC XML and submits it to CDS
         - calls associateIndicoIDToLOID(),
                 which associates the chosen IndicoID to the existing record of the LOID in micala DB
                 (no need to create a new record, because the user is only allowed to choose LOID's that are already in the micala DB)
         - calls submitMicalaMetadata(), which generates the micala lecture.xml and submits it to micala DB.
        All of these methods update their status to micala DB.
        """

        # Get the MARC XML and submit it to CDS,
        # then update micala database Status table showing task completed.
        # do this for both plain_video and web_lecture talks
        resultCreateCDSRecord = createCDSRecord(self._aw,
                                                self._IndicoID,
                                                self._LODBID,
                                                self._contentType,
                                                self._videoFormat,
                                                self._languages)
        if resultCreateCDSRecord["success"] == False:
            raise RecordingManagerException("CDS record creation failed.\n%s" % resultCreateCDSRecord["result"])
            return "CDS record creation aborted."

        if self._contentType == 'web_lecture':
            # Update the micala database to match the LODBID with the IndicoID
            # This only makes sense for web_lecture talks
            # (for plain_video, a record in Lectures should already have been created by createCDSRecord() )
            resultAssociateIndicoIDToLOID = MicalaCommunication.associateIndicoIDToLOID(self._IndicoID,
                                              self._params.get('LODBID', None))
            if resultAssociateIndicoIDToLOID["success"] == False:
                raise RecordingManagerException("micala database update failed.\n%s" % resultAssociateIndicoIDToLOID["result"])
                return "CDS record creation aborted."

            # Create lecture.xml and submit to micala server,
            # then update micala database Status table showing task completed
            # (this only makes sense if it is a web_lecture)
            resultSubmitMicalaMetadata = submitMicalaMetadata(self._aw,
                                                              self._IndicoID,
                                                              self._contentType,
                                                              self._LODBID,
                                                              self._params.get('LOID', None),
                                                              self._videoFormat,
                                                              self._languages)
            if resultSubmitMicalaMetadata["success"] == False:
                raise RecordingManagerException("CDS record creation failed.\n%s" % resultSubmitMicalaMetadata["result"])
                return "micala metadata creation aborted."

        return "Successfully updated micala database and submitted CDS record for creation."

class RMCreateIndicoLinkService(CollaborationPluginServiceBase):

    def _checkParams(self):
        CollaborationPluginServiceBase._checkParams(self) #puts the Conference in self._conf
        self._IndicoID = self._params.get('IndicoID',   None)
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
