# -*- coding: utf-8 -*-
##
## $Id: mail.py,v 1.4 2009/04/15 15:17:45 dmartinc Exp $
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
from MaKaC.common.utils import formatDateTime


class WebExNotificationBase(GenericNotification):
    """ Base class to build an email notification for the Recording request plugin.
    """
    def __init__(self, booking):
        GenericNotification.__init__(self)
        
        self._booking = booking
        self._bp = booking._bookingParams
        self._conference = booking.getConference()
        
        self._modifLink = str(booking.getModificationURL())
        
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setContentType("text/html")
    
    def _getBookingDetails(self, typeOfMail):
        bp = self._bp
        
        return """
Request details:<br />
<table style="border-spacing: 10px 10px;">
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Booking id:</strong>
        </td>
        <td style="vertical-align: top;">
            %(id)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Creation date:</strong>
        </td>
        <td style="vertical-align: top;">
            %(creation_date)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Meeting title:</strong>
        </td>
        <td style="vertical-align: top;">
            %(title)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Meeting description:</strong>
        </td>
        <td style="vertical-align: top;">
            %(description)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Start date:</strong>
        </td>
        <td style="vertical-align: top">
            %(start_date)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>End date:</strong>
        </td>
        <td style="vertical-align: top">
            %(end_date)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Access password yes/no:</strong>
        </td>
        <td style="vertical-align: top">
            %(password)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Auto-join URL:</strong>
        </td>
        <td style="vertical-align: top">
            %(url)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Call-in phone number:</strong>
        </td>
        <td style="vertical-align: top">
            %(phone)s
        </td>
    </tr>
</table>
"""%({ "id":self._booking.getId(),
     "creation_date": MailTools.bookingCreationDate(self._booking),
#     "modification_date":MailTools.bookingModificationDate(self._booking, typeOfMail),
     "title":bp["meetingTitle"],
     "description":bp["meetingDescription"],
     "start_date":formatDateTime(self._booking.getAdjustedStartDate()),
     "end_date":formatDateTime(self._booking.getAdjustedEndDate()),
     "password":self._getHasAccessPassword(),
     "url":self._booking._url, 
     "phone":self._booking._phoneNum
       }
     )
        
    @classmethod
    def listToStr(cls, list):
        return "<br />".join([("•" + item) for item in list])
    
    def _getHasAccessPassword(self):
        if self._booking.getHasAccessPassword():
            return 'Yes'
        else:
            return 'No'
    
    def _getAutoJoinURL(self, typeOfMail):
        if typeOfMail == "remove":
            return "(booking deleted)"
        else:
            url = self._booking.getURL() 
            if url:
                return url
            else:
                return "No auto-join url. Maybe the WebEx booking is invalid"  
class WebExParticipantNotification(WebExNotificationBase):
    def __init__(self, booking, emailList, typeOfMail, changes=None): 
        WebExNotificationBase.__init__(self, booking)
        self.setToList(emailList)
        body_text = ""
        if typeOfMail == 'modify':
            self.setSubject("""[Indico] Modification to WebEx meeting: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
            body_text = "There has been a change to the WebEx meeting %s (event id: %s).  The new information is as follows. " % (self._conference.getTitle(), str(self._conference.getId()))
        elif typeOfMail == 'new':
            self.setSubject("""[Indico] New WebEx meeting: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
            body_text = "A new WebEx meeting %s (event id: %s) has been created.  The new information is as follows. " % (self._conference.getTitle(), str(self._conference.getId()))
        elif typeOfMail == 'delete':
            self.setSubject("""[Indico] WebEx meeting deleted: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
            body_text = "A new WebEx meeting %s (event id: %s) has been deleted.  The information is as follows. " % (self._conference.getTitle(), str(self._conference.getId()))
        if changes != None:
            body_text += "Changes to modification: <br/>" + self.listToStr( changes )
        body_text += self._getBookingDetails(typeOfMail)
        self.setBody( body_text )  
        return None


class WebExAdminNotificationBase(WebExNotificationBase):
    def __init__(self, booking):
        WebExNotificationBase.__init__(self, booking)
        self.setToList(MailTools.getAdminEmailList('WebEx'))

class WebExEventManagerNotificationBase(WebExNotificationBase):
    def __init__(self, booking):
        WebExNotificationBase.__init__(self, booking)
        self.setToList(MailTools.getManagersEmailList(self._conference, 'WebEx'))


class NewWebExMeetingNotificationAdmin(WebExAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """
    
    def __init__(self, booking):
        WebExAdminNotificationBase.__init__(self, booking)
        
        self.setSubject("""[WebEx] New WebEx meeting: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody("""Dear WebEx Responsible,<br />
<br />
There is a <strong>new WebEx meeting</strong> in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to see it in Indico.<br />
<br />
%s
<br />
%s
<br />
<br />
%s
""" % ( MailTools.getServerName(),
        MailTools.getServerName(),
        self._modifLink,
        MailTools.eventDetails(self._conference),
        MailTools.organizerDetails(self._conference),
        self._getBookingDetails('new')
        ))
        
class NewWebExMeetingNotificationManager(WebExEventManagerNotificationBase):
    """ Template to build an email notification to the conference manager
    """
    
    def __init__(self, booking):
        WebExEventManagerNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Indico] New WebEx meeting: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody("""Dear Conference Manager,<br />
<br />
There is a <strong>new EVO meeting</strong> in your conference.<br />
Click <a href="%s">here</a> to see it in Indico.<br />
<br />
%s
<br />
<br />
%s
<br />
Please note that the auto-join URL will not work until the EVO meeting time arrives.
""" % ( self._modifLink,
        MailTools.eventDetails(self._conference),
        self._getBookingDetails('new')
        ))
        
        
        
class WebExMeetingModifiedNotificationAdmin(WebExAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """
    
    def __init__(self, booking):
        WebExAdminNotificationBase.__init__(self, booking)
        
        self.setSubject("""[WebEx] WebEx meeting modified: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody("""Dear WebEx Responsible,<br />
<br />
An WebEx meeting <strong>was modified</strong> in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to see it in Indico.<br />
<br />
%s
<br />
%s
<br />
<br />
%s
""" % ( MailTools.getServerName(),
        MailTools.getServerName(),
        self._modifLink,
        MailTools.eventDetails(self._conference),
        MailTools.organizerDetails(self._conference),
        self._getBookingDetails('modify')
        ))
        
        
class WebExMeetingModifiedNotificationManager(WebExEventManagerNotificationBase):
    """ Template to build an email notification to the responsible
    """
    
    def __init__(self, booking):
        EVOEventManagerNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Indico] WebEx meeting modified: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody("""Dear Conference Manager,<br />
<br />
An WebEx meeting <strong>was modified</strong> in your conference.<br />
Click <a href="%s">here</a> to see it in Indico.<br />
<br />
%s
<br />
<br />
%s
<br />
Please note that the auto-join URL will not work until the EVO meeting time arrives.
""" % ( self._modifLink,
        MailTools.eventDetails(self._conference),
        self._getBookingDetails('modify')
        ))
        
        
        
class WebExMeetingRemovalNotificationAdmin(WebExAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """
    
    def __init__(self, booking):
        WebExAdminNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Indico] WebEx meeting deleted: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody("""Dear WebEx Responsible,<br />
<br />
A WebEx meeting <strong>was deleted</strong> in <a href="%s">%s</a><br />
<br />
%s
<br />
%s
<br />
<br />
%s
""" % ( MailTools.getServerName(),
        MailTools.getServerName(),
        MailTools.eventDetails(self._conference),
        MailTools.organizerDetails(self._conference),
        self._getBookingDetails('remove')
        ))
        
class WebExMeetingRemovalNotificationManager(WebExEventManagerNotificationBase):
    """ Template to build an email notification to the responsible
    """
    
    def __init__(self, booking):
        WebExEventManagerNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Indico] WebEx Meeting deleted %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody("""Dear Conference Manager,<br />
<br />
A WebEx meeting <strong>was deleted</strong> in your conference.<br />
<br />
%s
<br />
You also can see a list of all the EVO meetings here: (not implemented yet).<br />
<br />
<br />
%s
""" % ( MailTools.eventDetails(self._conference),
        self._getBookingDetails('remove')
        ))
