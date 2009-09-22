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
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.webinterface import urlHandlers
from MaKaC.common.utils import formatDateTime
from MaKaC.plugins.base import PluginsHolder

def needToSendEmails():
    evo = PluginsHolder().getPluginType('Collaboration').getPlugin('EVO')
    
    admins = evo.getOption('admins').getValue()
    sendMailNotifications = evo.getOption('sendMailNotifications').getValue()
    additionalEmails = evo.getOption('additionalEmails').getValue()
    
    return (sendMailNotifications and len(admins) > 0) or len(additionalEmails) > 0

class EVONotificationBase(GenericNotification):
    """ Base class to build an email notification for the Recording request plugin.
    """
    def __init__(self, booking):
        GenericNotification.__init__(self)
        
        self._booking = booking
        self._bp = booking._bookingParams
        self._conference = booking.getConference()
        
        self._displayLink = urlHandlers.UHConferenceDisplay.getURL(self._conference)
        self._adminLink = urlHandlers.UHConfModifCollaboration.getURL(self._conference,
                                                                      secure = CollaborationTools.isUsingHTTPS(),
                                                                      tab = CollaborationTools.getPluginTab(booking.getPlugin()))
        
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setContentType("text/html")
        
    def _getEventDetails(self):
        return """
Event details:
<table style="border-spacing: 10px 10px;">
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Event name:</strong>
        </td>
        <td>
            %s <a href="%s">(link)</a>
        </td
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Event id</strong>
        </td>
        <td>
            %s
        </td
    </tr>
</table>
"""%(self._conference.getTitle(),
     self._displayLink,
     self._conference.getId()
     )

    def _getOrganizerDetails(self):
        creator = self._conference.getCreator()
        
        additionalEmailsText = ""
        additionalEmails = creator.getSecondaryEmails()
        if additionalEmails:
            additionalEmailsText="""
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Additional emails:</strong>
        </td>
        <td>
            %s
        </td
    </tr>
""" % ", ".join(creator.getEmails()[1:])

        additionalTelephonesText = ""
        additionalTelephones = creator.getSecondaryTelephones()
        if additionalTelephones:
            additionalTelephonesText="""
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Additional telephones:</strong>
        </td>
        <td>
            %s
        </td
    </tr>
""" % ", ".join(creator.getTelephone()[1:])

        
        return """
Creator of the event details:
<table style="border-spacing: 10px 10px;">
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Full name:</strong>
        </td>
        <td>
            %s
        </td
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Main email address:</strong>
        </td>
        <td>
            %s
        </td
    </tr>
    %s
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Main phone number:</strong>
        </td>
        <td>
            %s
        </td
    </tr>
    %s
</table>
""" % (creator.getFullName(),
       creator.getEmail(),
       additionalEmailsText,
       creator.getTelephone(),
       additionalTelephonesText
       )
    
    def _getCreationDate(self):
        return formatDateTime(self._booking.getAdjustedCreationDate())
    
    def _getModificationDateRow(self, typeOfMail):
        if (typeOfMail == 'new'):
            return ""
        else:
            return """
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Modification date:</strong>
        </td>
        <td style="vertical-align: top;">
            %s
        </td>
    </tr>
""" % formatDateTime(self._booking.getAdjustedModificationDate())

        
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
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Creation date:</strong>
        </td>
        <td style="vertical-align: top;">
            %s
        </td>
    </tr>
    %s
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Meeting title:</strong>
        </td>
        <td style="vertical-align: top;">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Meeting description:</strong>
        </td>
        <td style="vertical-align: top;">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Community:</strong>
        </td>
        <td style="vertical-align: top;">
            %s (id: %s)
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Start date:</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>End date:</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Access password yes/no:</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Auto-join URL:</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
</table>
"""%(self._booking.getId(),
     self._getCreationDate(),
     self._getModificationDateRow(typeOfMail),
     bp["meetingTitle"],
     bp["meetingDescription"],
     self._booking.getCommunityName(),
     bp["communityId"],
     formatDateTime(self._booking.getAdjustedStartDate()),
     formatDateTime(self._booking.getAdjustedEndDate()),
     self._getHasAccessPassword(),
     self._getAutoJoinURL(typeOfMail)
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
                return "No auto-join url. Maybe the EVO booking is invalid"  


class EVOAdminNotificationBase(EVONotificationBase):
    def __init__(self, booking):
        EVONotificationBase.__init__(self, booking)
        adminEmails = [u.getEmail() for u in booking.getPluginOptionByName('admins').getValue()]
        additionalEmails = booking.getPluginOptionByName("additionalEmails").getValue()
        self.setToList(adminEmails + additionalEmails)
        
class EVOEventManagerNotificationBase(EVONotificationBase):
    def __init__(self, booking):
        EVONotificationBase.__init__(self, booking)
        self.setToList([u.getEmail() for u in self._conference.getManagerList()])


class NewEVOMeetingNotificationAdmin(EVOAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """
    
    def __init__(self, booking):
        EVOAdminNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Indico] [New EVO meeting] %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody("""Dear EVO Responsible,<br />
<br />
There is a <strong>new EVO meeting</strong>.<br />
Click <a href="%s">here</a> to see it in Indico.<br />
<br />
%s
<br />
%s
<br />
You also can see a list of all the EVO meetings here: (not implemented yet).<br />
<br />
<br />
%s
""" % ( self._adminLink,
        self._getEventDetails(),
        self._getOrganizerDetails(),
        self._getBookingDetails('new')
        ))
        
class NewEVOMeetingNotificationManager(EVOEventManagerNotificationBase):
    """ Template to build an email notification to the conference manager
    """
    
    def __init__(self, booking):
        EVOEventManagerNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Indico] [New EVO meeting] %s (event id: %s)"""
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
""" % ( self._adminLink,
        self._getEventDetails(),
        self._getBookingDetails('new')
        ))
        
        
        
class EVOMeetingModifiedNotificationAdmin(EVOAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """
    
    def __init__(self, booking):
        EVOAdminNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Indico] [Modified EVO meeting] %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody("""Dear EVO Responsible,<br />
<br />
An EVO meeting <strong>was modified</strong>.<br />
Click <a href="%s">here</a> to see it in Indico.<br />
<br />
%s
<br />
%s
<br />
You also can see a list of all the EVO meetings here: (not implemented yet).<br />
<br />
<br />
%s
""" % ( self._adminLink,
        self._getEventDetails(),
        self._getOrganizerDetails(),
        self._getBookingDetails('modify')
        ))
        
        
class EVOMeetingModifiedNotificationManager(EVOEventManagerNotificationBase):
    """ Template to build an email notification to the responsible
    """
    
    def __init__(self, booking):
        EVOEventManagerNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Indico] [Modified EVO meeting] %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody("""Dear Conference Manager,<br />
<br />
An EVO meeting <strong>was modified</strong> in your conference.<br />
Click <a href="%s">here</a> to see it in Indico.<br />
<br />
%s
<br />
<br />
%s
<br />
Please note that the auto-join URL will not work until the EVO meeting time arrives.
""" % ( self._adminLink,
        self._getEventDetails(),
        self._getBookingDetails('modify')
        ))
        
        
        
class EVOMeetingRemovalNotificationAdmin(EVOAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """
    
    def __init__(self, booking):
        EVOAdminNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Indico] [Deleted EVO meeting] %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody("""Dear EVO Responsible,<br />
<br />
An EVO meeting <strong>was deleted</strong>.<br />
<br />
%s
<br />
%s
<br />
You also can see a list of all the EVO meetings here: (not implemented yet).<br />
<br />
<br />
%s
""" % ( self._getEventDetails(),
        self._getOrganizerDetails(),
        self._getBookingDetails('remove')
        ))
        
class EVOMeetingRemovalNotificationManager(EVOEventManagerNotificationBase):
    """ Template to build an email notification to the responsible
    """
    
    def __init__(self, booking):
        EVOEventManagerNotificationBase.__init__(self, booking)
        
        self.setSubject("""[Indico] [Deleted EVO meeting] %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        
        self.setBody("""Dear Conference Manager,<br />
<br />
An EVO meeting <strong>was deleted</strong> in your conference.<br />
<br />
%s
<br />
You also can see a list of all the EVO meetings here: (not implemented yet).<br />
<br />
<br />
%s
""" % ( self._getEventDetails(),
        self._getBookingDetails('remove')
        ))