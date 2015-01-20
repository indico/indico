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
from MaKaC.plugins.Collaboration.collaborationTools import MailTools

from indico.core.config import Config
from MaKaC.plugins.Collaboration.WebEx.common import getWebExOptionValueByName
import re

class WebExNotificationBase(GenericNotification):
    """ Base class to build an email notification for the Recording request plugin.
    """
    def __init__(self, booking):
        GenericNotification.__init__(self)

        self._booking = booking
        self._bp = booking._bookingParams
        self._conference = booking.getConference()

        self._modifLink = str(booking.getModificationURL())

        self.setFromAddr("Indico Mailer<%s>" % Config.getInstance().getSupportEmail())
        self.setContentType("text/html")

    def _getBookingDetails(self):
        bp = self._bp

        return """
Request details:<br />
<table style="border-spacing: 10px 10px;">
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
            <strong>Agenda:</strong>
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
            %(start_date)s &nbsp;&nbsp;&nbsp;%(timezone)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Access password:</strong>
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
            <a href="%(url)s" target="_blank">%(url)s</a>
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;" colspan="2">
            To receive a call back, provide your phone number when you join the meeting,<br/>or call the number below and enter the access code.
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Call-in toll-free phone number:</strong>
        </td>
        <td style="vertical-align: top">
            %(phone)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Call-in toll number:</strong>
        </td>
        <td style="vertical-align: top">
            %(phoneToll)s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Access code:</strong>
        </td>
        <td style="vertical-align: top">
            %(phoneAccessCode)s
        </td>
    </tr>
</table>
"""%({ "title":bp["meetingTitle"],
     "description":bp["meetingDescription"],
     "start_date":self._booking.getAdjustedStartDate().strftime("%A, %d %B %Y. %I:%M %p"),
     "end_date":self._booking.getAdjustedEndDate().strftime("%A, %d %B %Y. %I:%M %p"),
     "password":self._booking.getAccessPassword(),
     "url":self._booking.getUrl(),
     "phone":self._booking.getPhoneNum(),
     "phoneToll":self._booking.getPhoneNumToll(),
     "phoneAccessCode":re.sub(r'(\d{3})(?=\d)',r'\1 ', str(self._booking.getWebExKey())[::-1])[::-1],
     "timezone":self._booking._conf.getTimezone()
       }
     )

    @classmethod
    def listToStr(cls, li):
        return "<br />".join([("•" + item) for item in li])

class WebExParticipantNotification(WebExNotificationBase):
    def __init__(self, booking, emailList, typeOfMail, additionalText=""):
        WebExNotificationBase.__init__(self, booking)
        self.setToList(emailList)
        body_text = ""
#        changes=None
        if typeOfMail == 'modify':
            self.setSubject("""[Indico] Modification to WebEx meeting: %s""" % self._conference.getTitle())
            body_text = _("%s There has been a change to the WebEx meeting.  The new information is as follows. " % additionalText)
#            if len( booking.getLatestChanges() ) > 0:
#                body_text += "<ul>\n"
#                for change in booking.getLatestChanges():
#                    body_text += "<li>" + change + "</li>\n"
#                body_text += "</ul>\n"
        elif typeOfMail == 'new':
            self.setSubject("""[Indico] New WebEx meeting: %s""" % self._conference.getTitle())
            body_text = _("%s A new WebEx meeting has been created.  The information is as follows." % additionalText)
        elif typeOfMail == 'delete':
            self.setSubject("""[Indico] WebEx meeting deleted: %s""" % self._conference.getTitle())
            body_text = _("%s A WebEx meeting has been deleted.  The information is as follows." % additionalText)
#        if change != None:
#            body_text += _("Changes to the booking: <br/>") + self.listToStr( changes )
        body_text += self._getBookingDetails()
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
        self._getBookingDetails()
        ))

class NewWebExMeetingNotificationManager(WebExEventManagerNotificationBase):
    """ Template to build an email notification to the conference manager
    """

    def __init__(self, booking):
        if not getWebExOptionValueByName("sendMailNotifications"):
            return
        WebExEventManagerNotificationBase.__init__(self, booking)

        self.setSubject("""[Indico] New WebEx meeting: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Conference Manager,<br />
<br />
There is a <strong>new WebEx meeting</strong> in your conference.<br />
Click <a href="%s">here</a> to see it in Indico.<br />
<br />
%s
<br />
<br />
%s
<br />
Please note that the auto-join URL will not work until the WebEx meeting time arrives.
""" % ( self._modifLink,
        MailTools.eventDetails(self._conference),
        self._getBookingDetails()
        ))



class WebExMeetingModifiedNotificationAdmin(WebExAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """
    def __init__(self, booking):
        WebExAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[WebEx] WebEx meeting modified: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))


        body_text = "Dear WebEx Responsible,<br /> There has been a change on %s to the WebEx meeting %s. <br/><br/>" % (MailTools.getServerName(), self._conference.getTitle() )
#        if len( booking.getLatestChanges() ) > 0:
#            body_text += "<ul>\n"
#            for change in booking.getLatestChanges():
#                body_text += "<li>" + change + "</li>\n"
#            body_text += "</ul>\n"
        the_body2 = """
<br />
See the event page here: %s <br/>
The full details are below:
<br />
%s
<br />
%s
<br />
<br />
%s
""" % (
        self._modifLink,
        MailTools.eventDetails(self._conference),
        MailTools.organizerDetails(self._conference),
        self._getBookingDetails()
        )
        self.setBody(body_text + the_body2)

class WebExMeetingModifiedNotificationManager(WebExEventManagerNotificationBase):
    """ Template to build an email notification to the responsible
    """

    def __init__(self, booking):
        if not getWebExOptionValueByName("sendMailNotifications"):
            return
        WebExEventManagerNotificationBase.__init__(self, booking)

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
Please note that the auto-join URL will not work until the WebEx host starts the meeting.
""" % ( self._modifLink,
        MailTools.eventDetails(self._conference),
        self._getBookingDetails()
        ))



class WebExMeetingRemovalNotificationAdmin(WebExAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """

    def __init__(self, booking):
        WebExAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[WebEx] WebEx meeting deleted: %s (event id: %s)"""
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
        self._getBookingDetails()
        ))

class WebExMeetingRemovalNotificationManager(WebExEventManagerNotificationBase):
    """ Template to build an email notification to the responsible
    """

    def __init__(self, booking):
        if not getWebExOptionValueByName("sendMailNotifications"):
            return
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
        self._getBookingDetails()
        ))
