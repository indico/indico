# -*- coding: utf-8 -*-
##
## $Id: collaboration.py,v 1.12 2009/04/25 13:56:17 dmartinc Exp $
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

from MaKaC.plugins.Collaboration.base import CSBookingBase
from MaKaC.plugins.Collaboration.RecordingRequest.mail import NewRequestNotification, RequestModifiedNotification, RequestDeletedNotification,\
    needToSendEmails
from MaKaC.common.mail import GenericMailer
from MaKaC.plugins.Collaboration.RecordingRequest.common import RecordingRequestException,\
    RecordingRequestError
from MaKaC.common.logger import Logger

class CSBooking(CSBookingBase):
    
    _hasStart = False
    _hasStop = False
    _hasCheckStatus = True
    _hasAcceptReject = True
    
    _needsBookingParamsCheck = True
    
    _allowMultiple = False
    
    _hasStartDate = False
        
    def __init__(self, type, conf):
        CSBookingBase.__init__(self, type, conf)
        self._bookingParams = {
            "talks" : None,
            "talkSelectionComments": None,
            "talkSelection": [],
            "permission": None,
            "lectureOptions": [],
            "lectureStyle": None,
            "postingUrgency": None,
            "numRemoteViewers": 0,
            "numAttendees": 0,
            "recordingPurpose": [],
            "intendedAudience" : [],
            "subjectMatter": [],
            "otherComments": None
        }
    
    def _checkBookingParams(self):
        if not self._bookingParams["permission"]:
            raise RecordingRequestException("permission parameter cannot be left empty")
        if self._bookingParams["lectureOptions"] == 'chooseOne': #change when list of community names is ok
            raise RecordingRequestException("lectureOptions parameter cannot be 'chooseOne'")
        if self._bookingParams["lectureStyle"] == 'chooseOne': #change when list of community names is ok
            raise RecordingRequestException("lectureStyle parameter cannot be 'chooseOne'")
        return False

    def _create(self):
        self._statusMessage = "Request successfully sent"
        self._statusClass = "statusMessageOther"
        
        if needToSendEmails():
            try:
                notification = NewRequestNotification(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                     "MaKaC/plugins/Collaboration/RecordingRequest/collaboration.py",
                                     self.getConference().getCreator())
            except Exception,e:
                Logger.get('RecReq').error(
                    """Could not send NewRequestNotification for request with id %s , exception: %s""" % (self._id, str(e)))
                return RecordingRequestError('create', e)
        

    def _modify(self):
        self._statusMessage = "Request successfully sent"
        self._statusClass = "statusMessageOther"
        
        if needToSendEmails():
            try:
                notification = RequestModifiedNotification(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                     "MaKaC/plugins/Collaboration/RecordingRequest/collaboration.py",
                                     self.getConference().getCreator())
            except Exception,e:
                Logger.get('RecReq').error(
                    """Could not send RequestModifiedNotification for request with id %s , exception: %s""" % (self._id, str(e)))
                return RecordingRequestError('edit', e)

                                
    def _checkStatus(self):
        pass

    def _accept(self):
        self._statusMessage = "Request accepted"
        self._statusClass = "statusMessageOK"
        
    def _reject(self):
        self._statusMessage = "Request rejected by responsible"
        self._statusClass = "statusMessageError"
                                        
    def _delete(self):
        if needToSendEmails():
            try:
                notification = RequestDeletedNotification(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                     "MaKaC/plugins/Collaboration/RecordingRequest/collaboration.py",
                                     self.getConference().getCreator())
            except Exception,e:
                Logger.get('RecReq').error(
                    """Could not send RequestDeletedNotification for request with id %s , exception: %s""" % (self._id, str(e)))
                return RecordingRequestError('remove', e)
