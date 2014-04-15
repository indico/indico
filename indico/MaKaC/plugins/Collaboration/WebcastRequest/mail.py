# -*- coding: utf-8 -*-
##
##
## This file is par{t of Indico.
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
from MaKaC.webinterface.mail import GenericNotification

from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.plugins.Collaboration.collaborationTools import MailTools
from MaKaC.plugins.Collaboration.WebcastRequest.common import getCommonTalkInformation
from indico.core.config import Config
from indico.util.string import safe_upper


class WebcastRequestNotificationBase(GenericNotification):
    """ Base class to build an email notification for the Webcast request plugin.
    """
    def __init__(self, booking):
        GenericNotification.__init__(self)
        self._booking = booking
        self._bp = booking.getBookingParams()
        self._conference = booking.getConference()
        self._isLecture = self._conference.getType() == 'simple_event'

        self._modifLink = str(booking.getModificationURL())

        self.setFromAddr("Indico Mailer<%s>"%Config.getInstance().getSupportEmail())
        self.setContentType("text/html")

    def _getRequestDetails(self, typeOfMail):
        bp = self._bp

        return """
Request details:<br />
<table style="border-spacing: 10px 10px;">
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Request id:</strong>
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
            <strong>Talk(s) to be webcasted:</strong>
        </td>
        <td style="vertical-align: top;">
            %s
        </td>
    </tr>
    <tr>
        <td colspan="2">
            <strong>Audience:</strong><br />
            %s
        </td>
    </tr>
    <tr>
        <td colspan="2">
            <strong>Additional comments:</strong><br />
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>List of talks to be webcasted:</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
</table>
""" % (self._booking.getId(),
       MailTools.bookingCreationDate(self._booking),
       MailTools.bookingModificationDate(self._booking, typeOfMail),
       self._getTalksShortMessage(),
       self._bp["audience"] or _("No restriction"),
       self._getComments(),
       self._getTalks())

    def _getTalks(self):
        if self._isLecture:
            return """(This event is a lecture. Therefore, it has no talks)"""

        else:
            #"all" "choose" "neither"
            if self._bp["talks"] == "all":
                talkInfo = getCommonTalkInformation(self._conference)
                text = ["""The user chose "All webcast-able Talks". List of webcast-able talks:"""]
                webcastableTalks = talkInfo[3]
                if webcastableTalks:
                    text.extend(MailTools.talkListText(self._conference, webcastableTalks))
                    text.append("<strong>Important note:</strong> room is only shown if different from event.")
                else:
                    text.append("(This event has no webcast-able talks)")
                return "<br />".join(text)
            else:
                text = ["""The user chose the following talks:"""]
                selectedTalks = [self._conference.getContributionById(contribId) for contribId in self._bp["talkSelection"]]
                if selectedTalks:
                    text.extend(MailTools.talkListText(self._conference, selectedTalks))
                    text.append("<strong>Important note:</strong> room is only shown if different from event.")
                else:
                    text.append("(User did not choose any talks)")

                return "<br />".join(text)

    def _getTalksShortMessage(self):
        if self._isLecture:
            return """(This event is a lecture. Therefore, it has no talks)"""
        else:
            if self._bp["talks"] == "all":
                return """The user chose "All webcast-able Talks". The list of all talks can be found at the end of this e-mail."""
            elif self._bp["talks"] == "neither":
                return """Please see the talk selection comments"""
            else:
                return """The user chose "Choose talks". The list of chosen talks can be found at the end of this e-mail."""

    def _getComments(self):
        comments = self._bp["otherComments"].strip()
        if comments:
            return comments
        return "(User didn't write any comments)"

class WebcastRequestAdminNotificationBase(WebcastRequestNotificationBase):
    """ Base class to build an email notification to Admins
    """
    def __init__(self, booking):
        WebcastRequestNotificationBase.__init__(self, booking)
        self.setToList(MailTools.getAdminEmailList('WebcastRequest'))


class WebcastRequestManagerNotificationBase(WebcastRequestNotificationBase):
    """ Base class to build an email notification to Users
    """
    def __init__(self, booking):
        WebcastRequestNotificationBase.__init__(self, booking)
        self.setToList(MailTools.getManagersEmailList(self._conference, 'WebcastRequest'))

class NewRequestNotification(WebcastRequestAdminNotificationBase):
    """ Template to build an email notification to the webcast responsible
    """

    def __init__(self, booking):
        WebcastRequestAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[WebcastReq] New webcast request: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        self.setBody("""Dear Webcast Manager,<br />
<br />
There is a <strong>new webcast request</strong> in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to accept or reject the request.<br />
%s
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
        MailTools.currentUserDetails('Requester'),
        MailTools.organizerDetails(self._conference),
        self._getRequestDetails('new')
        ))



class RequestModifiedNotification(WebcastRequestAdminNotificationBase):
    """ Template to build an email notification to the webcast responsible
    """

    def __init__(self, booking):
        WebcastRequestAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[WebcastReq] Webcast request modified: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Webcast Manager,<br />
<br />
A webcast request <strong>has been modified</strong> in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to accept or reject the request.<br />
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
        self._getRequestDetails('modify')
        ))


class RequestRescheduledNotification(WebcastRequestAdminNotificationBase):
    """ Template to build an email notification to the webcast responsible
    """

    def __init__(self, booking):
        WebcastRequestAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[WebcastReq] Webcast request rescheduled: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Webcast Manager,<br />
<br />
A webcast request <strong>has been rescheduled</strong> in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to view the request.<br />
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
        self._getRequestDetails('modify')
        ))


class RequestRelocatedNotification(WebcastRequestAdminNotificationBase):
    """ Template to build an email notification to the webcast responsible
    """

    def __init__(self, booking):
        WebcastRequestAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[WebcastReq] Webcast request relocated: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Webcast Manager,<br />
<br />
A webcast request <strong>has been relocated</strong> in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to view the request.<br />
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
        self._getRequestDetails('modify')
        ))



class RequestDeletedNotification(WebcastRequestAdminNotificationBase):
    """ Template to build an email notification to the webcast responsible
    """

    def __init__(self, booking):
        WebcastRequestAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[WebcastReq] Webcast request deleted: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Webcast Manager,<br />
<br />
A webcast request <strong>has been withdrawn</strong> in <a href="%s">%s</a><br />
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
        self._getRequestDetails('remove')
        ))

class RequestAcceptedNotification(WebcastRequestManagerNotificationBase):
    """ Template to build an email notification to the event managers
        when a request gets accepted.
    """


    def __init__(self, booking):
        WebcastRequestManagerNotificationBase.__init__(self, booking)

        self.setSubject("""[Indico] Webcast request accepted: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Event Manager,<br />
<br />
Your webcast request for the event: "%s" has been accepted.<br />
Click <a href="%s">here</a> to view your request.<br />
<br />
Best Regards,<br />
Webcast Managers

""" % ( self._conference.getTitle(),
        self._modifLink
        ))

class RequestAcceptedNotificationAdmin(WebcastRequestAdminNotificationBase):
    """ Template to build an email notification to the admins when a request gets accepted
    """

    def __init__(self, booking, user = None):
        WebcastRequestAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[WebcastReq] Webcast request accepted: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        userInfo = ""
        if user:
            userInfo = " by %s %s" % (user.getFirstName(), safe_upper(user.getFamilyName()))
        self.setBody("""Dear Webcast Manager,<br />
<br />
A webcast request for the event: "%s" has been accepted in <a href="%s">%s</a>""" %(self._conference.getTitle(),
                                                                                    MailTools.getServerName(),
                                                                                    MailTools.getServerName())
+ userInfo + """.<br />
Click <a href="%s">here</a> to view the request.<br />

""" % (self._modifLink))


class RequestRejectedNotification(WebcastRequestManagerNotificationBase):
    """ Template to build an email notification to the event managers
        when a request gets accepted.
    """


    def __init__(self, booking):

        WebcastRequestManagerNotificationBase.__init__(self, booking)

        self.setSubject("""[Indico] Webcast request rejected: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        self.setBody("""Dear Event Manager,<br />
<br />
Your webcast request for the event: "%s" has been rejected.<br />
Click <a href="%s">here</a> to view your request.<br />
<br />
The reason given by the Webcast manager was:
<br />
%s
<br />
<br />
Best Regards,<br />
Webcast Managers
""" % ( self._conference.getTitle(),
        self._modifLink,
        self._booking.getRejectReason().strip()
        ))

class RequestRejectedNotificationAdmin(WebcastRequestAdminNotificationBase):
    """ Template to build an email notification to the admins when a request gets accepted
    """

    def __init__(self, booking):
        WebcastRequestAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[WebcastReq] Webcast request rejected: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Webcast Manager,<br />
<br />
A webcast request for the event: "%s" has been rejected in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to view the request.<br />
<br />
The reason given by the Webcast Manager who rejected the request was:
<br />
%s
<br />

""" % ( self._conference.getTitle(),
        MailTools.getServerName(),
        MailTools.getServerName(),
        self._modifLink,
        self._booking.getRejectReason().strip()
      ))
