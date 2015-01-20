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

from MaKaC.plugins.Collaboration.services import CollaborationPluginServiceBase
from MaKaC.plugins.Collaboration.RecordingManager.exceptions import RecordingManagerException
from MaKaC.plugins.Collaboration.RecordingManager.common import createIndicoLink, createCDSRecord, submitMicalaMetadata
from MaKaC.plugins.Collaboration.RecordingManager.micala import MicalaCommunication

class RMCreateCDSRecordService(CollaborationPluginServiceBase):

    def _checkParams(self):
        CollaborationPluginServiceBase._checkParams(self) #puts the Conference in self._conf
        self._IndicoID        = self._params.get('IndicoID',        None)
        self._LOID            = self._params.get('LOID',            None)
        self._LODBID          = self._params.get('LODBID',          None)
        self._lectureTitle    = self._params.get('lectureTitle',    None)
        self._lectureSpeakers = self._params.get('lectureSpeakers', None)
        self._confId          = self._params.get('conference',      None)
        self._videoFormat     = self._params.get('videoFormat',     None)
        self._contentType     = self._params.get('contentType',     None)
        self._languages       = self._params.get('languages',       None)

        if not self._contentType:
            raise RecordingManagerException(_("No content type supplied (plain video or web lecture)"))
        if not self._IndicoID:
            raise RecordingManagerException(_("No IndicoID supplied"))

        if self._contentType == 'web_lecture':
            if not self._LODBID:
                raise RecordingManagerException(_("No LODBID supplied"))
        elif self._contentType == 'plain_video':
            if not self._videoFormat:
                raise RecordingManagerException(_("No video format supplied"))

        if not self._confId:
            raise RecordingManagerException(_("No conference ID supplied"))

        if not self._languages:
            raise RecordingManagerException(_("No languages supplied"))

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
                                                self._lectureTitle,
                                                self._lectureSpeakers,
                                                self._contentType,
                                                self._videoFormat,
                                                self._languages)
        if resultCreateCDSRecord["success"] == False:
            raise RecordingManagerException(_("CDS record creation failed.\n%s") % resultCreateCDSRecord["result"])
            return _("CDS record creation aborted.")

        if self._contentType == 'web_lecture':
            # Update the micala database to match the LODBID with the IndicoID
            # This only makes sense for web_lecture talks
            # (for plain_video, a record in Lectures should already have been created by createCDSRecord() )
            resultAssociateIndicoIDToLOID = MicalaCommunication.associateIndicoIDToLOID(self._IndicoID,
                                              self._params.get('LODBID', None))
            if resultAssociateIndicoIDToLOID["success"] == False:
                raise RecordingManagerException(_("micala database update failed.\n%s") % resultAssociateIndicoIDToLOID["result"])
                return _("CDS record creation aborted.")

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
                raise RecordingManagerException(_("CDS record creation failed.\n%s") % resultSubmitMicalaMetadata["result"])
                return _("micala metadata creation aborted.")

        return _("Successfully updated micala database and submitted CDS record for creation.")

class RMCreateIndicoLinkService(CollaborationPluginServiceBase):

    def _checkParams(self):
        CollaborationPluginServiceBase._checkParams(self) #puts the Conference in self._conf
        self._IndicoID = self._params.get('IndicoID',   None)
        self._confId   = self._params.get('conference', None)
        self._CDSID    = self._params.get('CDSID',      None)

        if not self._IndicoID:
            raise RecordingManagerException(_("No IndicoID supplied"))
        if not self._confId:
            raise RecordingManagerException(_("No conference ID supplied"))
        if not self._CDSID:
            raise RecordingManagerException(_("No CDS record ID supplied"))

    def _getAnswer(self):
        # Create the Indico link
        createIndicoLink(self._IndicoID, self._CDSID)

        return 'None' # wtf, but let's keep the return value there used to be before..

# In case we want to update list of orphans after page has loaded...
class RMOrphansService(CollaborationPluginServiceBase):

    def _getAnswer(self):
        pass
        #orphans = getOrphans()
