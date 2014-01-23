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
from MaKaC.common.utils import formatDateTime
from indico.core.config import Config

class EVONotificationBase(GenericNotification):
    """ Base class to build an email notification for the Recording request plugin.
    """
    def __init__(self, booking):
        GenericNotification.__init__(self)

        self._booking = booking
        self._bp = booking._bookingParams
        self._conference = booking.getConference()

        self._modifLink = str(booking.getModificationURL())

        self.setFromAddr("Indico Mailer <%s>"%Config.getInstance().getSupportEmail())
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
            <strong>Phone bridge ID:</strong>
        </td>
        <td style="vertical-align: top;">
            %s
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
     MailTools.bookingCreationDate(self._booking),
     MailTools.bookingModificationDate(self._booking, typeOfMail),
     bp["meetingTitle"],
     bp["meetingDescription"],
     self._booking.getCommunityName(),
     bp["communityId"],
     self._booking.getPhoneBridgeId(),
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
            return 'Yes (see booking in Indico)'
        else:
            return 'No'

    def _getAutoJoinURL(self, typeOfMail):
        if typeOfMail == "remove":
            return "(booking deleted)"
        else:
            url = self._booking.getUrl()
            if url:
                return url
            else:
                return "No auto-join url. Maybe the EVO booking is invalid"


class EVOAdminNotificationBase(EVONotificationBase):
    def __init__(self, booking):
        EVONotificationBase.__init__(self, booking)
        self.setToList(MailTools.getAdminEmailList('EVO'))
        self.setCCList(MailTools.getAdminEmailList())

class EVOEventManagerNotificationBase(EVONotificationBase):
    def __init__(self, booking):
        EVONotificationBase.__init__(self, booking)
        self.setToList(MailTools.getManagersEmailList(self._conference, 'EVO'))


class NewEVOMeetingNotificationAdmin(EVOAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """

    def __init__(self, booking):
        EVOAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[EVO] New EVO meeting: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear EVO Manager,<br />
<br />
There is a <strong>new EVO meeting</strong> in <a href="%s">%s</a><br />
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

class NewEVOMeetingNotificationManager(EVOEventManagerNotificationBase):
    """ Template to build an email notification to the conference manager
    """

    def __init__(self, booking):
        EVOEventManagerNotificationBase.__init__(self, booking)

        self.setSubject("""[Indico] New EVO meeting: %s (event id: %s)"""
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



class EVOMeetingModifiedNotificationAdmin(EVOAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """

    def __init__(self, booking):
        EVOAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[EVO] EVO meeting modified: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear EVO Manager,<br />
<br />
An EVO meeting <strong>was modified</strong> in <a href="%s">%s</a><br />
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


class EVOMeetingModifiedNotificationManager(EVOEventManagerNotificationBase):
    """ Template to build an email notification to the responsible
    """

    def __init__(self, booking):
        EVOEventManagerNotificationBase.__init__(self, booking)

        self.setSubject("""[Indico] EVO meeting modified: %s (event id: %s)"""
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
""" % ( self._modifLink,
        MailTools.eventDetails(self._conference),
        self._getBookingDetails('modify')
        ))



class EVOMeetingRemovalNotificationAdmin(EVOAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """

    def __init__(self, booking):
        EVOAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[EVO] EVO meeting deleted: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear EVO Manager,<br />
<br />
An EVO meeting <strong>was deleted</strong> in <a href="%s">%s</a><br />
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

class EVOMeetingRemovalNotificationManager(EVOEventManagerNotificationBase):
    """ Template to build an email notification to the responsible
    """

    def __init__(self, booking):
        EVOEventManagerNotificationBase.__init__(self, booking)

        self.setSubject("""[Indico] EVO Meeting deleted %s (event id: %s)"""
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
""" % ( MailTools.eventDetails(self._conference),
        self._getBookingDetails('remove')
        ))
