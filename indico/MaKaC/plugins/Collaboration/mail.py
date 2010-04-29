# -*- coding: utf-8 -*-
##
##
## This file is par{t of CDS Indico.
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

from MaKaC.webinterface.mail import GenericNotification
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.plugins.Collaboration.collaborationTools import MailTools
from MaKaC.common.TemplateExec import beautify

class CollaborationNotificationBase(GenericNotification):
    """ Base class to build an email notification for the Recording request plugin.
    """
    def __init__(self, booking):
        GenericNotification.__init__(self)
        
        self._booking = booking
        self._bp = booking._bookingParams
        self._conference = booking.getConference()
        
        self._modifLink = str(self._booking.getModificationURL())
        
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setToList(MailTools.getAdminEmailList())
        self.setContentType("text/html")
        
    def _getBookingDetails(self, typeOfMail):
        return """
Booking / request details:<br />
<table style="border-spacing: 10px 10px;">
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Type:</strong>
        </td>
        <td style="vertical-align: top;">
            %(type)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>id:</strong>
        </td>
        <td style="vertical-align: top;">
            %(id)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Modification link:</strong>
        </td>
        <td style="vertical-align: top;">
            <a href="%(modifURL)s">link</a>
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Creation date:</strong>
        </td>
        <td style="vertical-align: top;">
            %(creationDate)s
        </td>
    </tr>
    %(modificationDate)s
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Booking parameters:</strong>
        </td>
        <td style="vertical-align: top;">
            %(bookingParams)s
        </td>
    </tr>
</table>
"""%{"type": self._booking.getType(),
     "id" : self._booking.getId(),
     "modifURL": self._modifLink,
     "creationDate": MailTools.bookingCreationDate(self._booking),
     "modificationDate": MailTools.bookingModificationDate(self._booking, typeOfMail),
     "bookingParams": beautify(self._bp)
     }


class NewBookingNotification(CollaborationNotificationBase):
    """ Template to build an email notification to a Collaboration responsible
    """
    
    def __init__(self, booking):
        CollaborationNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Video Services] New booking / request: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody(
"""
A new booking / request was created in <a href="%s">%s</a>
<br /><br />
%s
<br /><br />
%s
<br /><br />
%s
""" % ( MailTools.getServerName(),
        MailTools.getServerName(),
        self._getBookingDetails('new'),
        MailTools.eventDetails(self._conference),
        MailTools.organizerDetails(self._conference)
        ))
        
        
        
class BookingModifiedNotification(CollaborationNotificationBase):
    """ Template to build an email notification to a Collaboration responsible
    """
    
    def __init__(self, booking):
        CollaborationNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Video Services] Booking / request modified: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody(
"""
A booking / request was modified in <a href="%s">%s</a>
<br /><br />
%s
<br /><br />
%s
<br /><br />
%s
""" % ( MailTools.getServerName(),
        MailTools.getServerName(),
        self._getBookingDetails('modify'),
        MailTools.eventDetails(self._conference),
        MailTools.organizerDetails(self._conference)
        ))
        
        
        
class BookingDeletedNotification(CollaborationNotificationBase):
    """ Template to build an email notification to a Collaboration responsible
    """
    
    def __init__(self, booking):
        CollaborationNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Video Services] Booking / request deleted: %s (event id: %s)"""
                % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody(
"""
A booking / request was deleted in <a href="%s">%s</a>
<br /><br />
%s
<br /><br />
%s
<br /><br />
%s
""" % ( MailTools.getServerName(),
        MailTools.getServerName(),
        self._getBookingDetails('remove'),
        MailTools.eventDetails(self._conference),
        MailTools.organizerDetails(self._conference)
        ))