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
from MaKaC.plugins.Collaboration.collaborationTools import MailTools, CollaborationTools
from MaKaC.plugins.Collaboration.Vidyo.common import VidyoTools, getVidyoOptionValue
from MaKaC.webinterface import urlHandlers
from MaKaC.user import Avatar, AvatarHolder
from MaKaC.common import info
from MaKaC.common.utils import formatDateTime
from MaKaC.common.timezoneUtils import getAdjustedDate
from MaKaC.common.mail import GenericMailer
from MaKaC.common.logger import Logger
from MaKaC.common.TemplateExec import escape
from indico.core.config import Config



############### E-mail templates ##############


class VidyoNotificationBase(GenericNotification):
    """ Base class to build an email notification for the Recording request plugin.
    """
    def __init__(self, booking):
        GenericNotification.__init__(self)

        self._booking = booking
        self._bp = booking.getBookingParams()
        self._conference = booking.getConference()

        self._modifLink = str(booking.getModificationURL())

        self.setFromAddr("Indico Mailer <%s>" % Config.getInstance().getSupportEmail())
        self.setContentType("text/html")

    def _getBookingDetails(self, typeOfMail):
        bp = self._bp

        return """
Public room details:<br />
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
            <strong>Public room name:</strong>
        </td>
        <td style="vertical-align: top;">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Room owner:</strong>
        </td>
        <td style="vertical-align: top;">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Public room description:</strong>
        </td>
        <td style="vertical-align: top;">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Pin yes/no:</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Manager chose to show PIN:</strong>
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
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Visibilty:</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
</table>
""" % (self._booking.getId(),
     MailTools.bookingCreationDate(self._booking),
     MailTools.bookingModificationDate(self._booking, typeOfMail),
     bp["roomName"],
     self._getOwnerText(),
     bp["roomDescription"],
     self._getHasPin(),
     self._getShowPin(),
     self._getAutoJoinURL(typeOfMail),
     self._getVisibility(),
     )

    @classmethod
    def listToStr(cls, list):
        return "<br />".join([("•" + item) for item in list])

    def _getOwnerText(self):
        owner = self._booking.getOwnerObject()
        if isinstance(owner, Avatar):
            return """%s (Vidyo account: %s) """ % (owner.getFullName(), self._booking.getOwnerAccount())
        else:
            return """ Vidyo account: %s. Does not correspond to an Indico user """ % self._booking.getOwnerAccount()

    def _getHasPin(self):
        if self._booking.getHasPin():
            return 'Yes'
        else:
            return 'No'

    def _getShowPin(self):
        if self._booking.getBookingParamByName("displayPin"):
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
                return "No auto-join url. Maybe the Vidyo booking is invalid"

    def _getVisibility(self):
        if self._booking.isHidden():
            return "Booking is hidden (NOT visible) in the event display page"
        else:
            return "Booking is visible in the event display page"


class VidyoAdminNotificationBase(VidyoNotificationBase):
    def __init__(self, booking):
        VidyoNotificationBase.__init__(self, booking)
        self.setToList(MailTools.getAdminEmailList('Vidyo'))
        self.setCCList(MailTools.getAdminEmailList())

class VidyoEventManagerNotificationBase(VidyoNotificationBase):
    def __init__(self, booking):
        VidyoNotificationBase.__init__(self, booking)
        self.setToList(MailTools.getManagersEmailList(self._conference, 'Vidyo'))


class NewVidyoPublicRoomNotificationAdmin(VidyoAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """

    def __init__(self, booking):
        VidyoAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[Vidyo] New Vidyo public room: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Vidyo Manager,<br />
<br />
There is a <strong>new Vidyo public room</strong> in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to see it in Indico.<br />
<br />
%s
<br />
%s
<br />
<br />
%s
""" % (MailTools.getServerName(),
       MailTools.getServerName(),
       self._modifLink,
       MailTools.eventDetails(self._conference),
       MailTools.organizerDetails(self._conference),
       self._getBookingDetails('new')
       ))


class VidyoPublicRoomModifiedNotificationAdmin(VidyoAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """

    def __init__(self, booking):
        VidyoAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[Vidyo] Vidyo public room modified: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Vidyo Manager,<br />
<br />
A Vidyo public room <strong>was modified</strong> in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to see it in Indico.<br />
<br />
%s
<br />
%s
<br />
<br />
%s
""" % (MailTools.getServerName(),
       MailTools.getServerName(),
       self._modifLink,
       MailTools.eventDetails(self._conference),
       MailTools.organizerDetails(self._conference),
       self._getBookingDetails('modify')
       ))


class VidyoPublicRoomRemovalNotificationAdmin(VidyoAdminNotificationBase):
    """ Template to build an email notification to the responsible
    """

    def __init__(self, booking):
        VidyoAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[Vidyo] Vidyo public room deleted: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Vidyo Manager,<br />
<br />
A Vidyo public room <strong>was deleted</strong> in <a href="%s">%s</a><br />
<br />
%s
<br />
%s
<br />
<br />
%s
""" % (MailTools.getServerName(),
       MailTools.getServerName(),
       MailTools.eventDetails(self._conference),
       MailTools.organizerDetails(self._conference),
       self._getBookingDetails('remove')
       ))


class VidyoCleaningNotification(VidyoAdminNotificationBase):
    """ Template to build an email notification to the admins
        when the amount of public rooms has exceeded a limit
    """

    def __init__(self, booking):
        VidyoAdminNotificationBase.__init__(self, booking)

        currentCount = VidyoTools.getEventEndDateIndex().getCount()

        self.setSubject("""[Vidyo] Too many public rooms (%s)"""
                        % str(currentCount))

        self.setBody("""Dear Vidyo Manager,<br />
<br />
There are currently %s Vidyo public rooms created by Indico in <a href="%s">%s</a>.<br />
The system was setup to send you a notification if this number was more than %s.<br />
Please go to the <a href="%s">Vidyo Plugin configuration</a> in the Server Admin interface
and press the "Clean old rooms" button.<br />
""" % (str(currentCount),
       MailTools.getServerName(),
       MailTools.getServerName(),
       getVidyoOptionValue("cleanWarningAmount"),
       str(urlHandlers.UHAdminPlugins.getURL(CollaborationTools.getCollaborationPluginType()))))


class VidyoCleaningDoneNotification(GenericNotification):
    """ Template to build an email notification to the admins
        when the amount of public rooms has exceeded a limit
    """

    def __init__(self, maxDate, previousTotal, newTotal, error = None, attainedDate = None):
        GenericNotification.__init__(self)
        self.setFromAddr("Indico Mailer <%s>" % Config.getInstance().getSupportEmail())
        self.setContentType("text/html")
        self.setToList(MailTools.getAdminEmailList('Vidyo'))
        serverTimezone = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()

        if error:
            self.setSubject("""[Vidyo] Old room cleaning failed: %s rooms deleted"""
                        % str(previousTotal - newTotal))
            self.setBody("""Dear Vidyo Manager,<br />
<br />
A cleanup of old Vidyo rooms in <a href="%s">%s</a> encountered the following error:%s<br />
"All rooms before %s (%s, server timezone) should have been deleted but only the date %s was reached.<br />
There were %s rooms before the operation and there are %s rooms left now.<br />
""" % (MailTools.getServerName(),
       MailTools.getServerName(),
       escape(str(error)),
       formatDateTime(getAdjustedDate(maxDate, tz=serverTimezone)),
       serverTimezone,
       formatDateTime(getAdjustedDate(attainedDate, tz=serverTimezone)),
       str(previousTotal),
       str(newTotal)))
        else:
            self.setSubject("""[Vidyo] Old room cleaning successful: %s rooms deleted"""
                        % str(previousTotal - newTotal))
            self.setBody("""Dear Vidyo Manager,<br />
<br />
A cleanup was successfully executed for old Vidyo rooms in <a href="%s">%s</a>.<br />
All rooms attached to events finishing before %s (%s, server timezone) were deleted in the Vidyo server.<br />
There were %s rooms before the operation and there are %s  rooms left now.<br />
""" % (MailTools.getServerName(),
       MailTools.getServerName(),
       formatDateTime(getAdjustedDate(maxDate, tz=serverTimezone)),
       serverTimezone,
       str(previousTotal),
       str(newTotal)))


class VidyoOwnerNotificationBase(GenericNotification):

    def _getOwnerTitleText(self):
        if self._owner.getTitle():
            return "%s " % self._owner.getTitle()
        else:
            return ""


class VidyoOwnerChosenNotification(VidyoOwnerNotificationBase):
    """ Template to build an email to the owner of a room
    """

    def __init__(self, booking):
        VidyoOwnerNotificationBase.__init__(self)
        self._booking = booking
        self._owner = booking.getOwnerObject()

        self.setFromAddr("Indico Mailer <%s>" % Config.getInstance().getSupportEmail())
        self.setContentType("text/html")

        event = booking.getConference()

        self.setToList([self._owner.getEmail()])

        self.setSubject("""[Indico] You are the owner of a Vidyo public room attached to the event: %s""" % event.getTitle() )

        self.setBody("""Dear %s%s,<br />
<br />
A new Vidyo room was created in <a href="%s">Indico</a> for the event <a href="%s">%s</a>.<br />
You have been chosen as Owner of this Vidyo public room.<br />
<br />
This means you can manage the room through the Vidyo Desktop application and you will be able to:<br />
 - Invite other users to the room,<br />
 - Lock or unlock the room,<br />
 - Fix a maximum number of attendees,<br />
 - Expel people out of the room,<br />
 - and other similar actions.<br />
<br />
You will not be able, however, to remove or modify the room from Indico, unless you also have management rights for the event.<br />
<br />
<a href="%s">Click here</a> to join the Vidyo room.<br />
<br />
Name of the room: %s<br />
Extension: %s<br />
PIN: %s<br />
Description: %s<br />
<br />
Thank you for using our system.<br />
""" %
                     (self._getOwnerTitleText(),
                      self._owner.getStraightFullName(),
                      MailTools.getServerName(),
                      urlHandlers.UHConferenceDisplay.getURL(event),
                      event.getTitle(),
                      booking.getURL(),
                      booking.getBookingParamByName("roomName"),
                      str(booking.getExtension()),
                      self._getPinText(),
                      booking.getBookingParamByName("roomDescription")))

    def _getPinText(self):
        if self._booking.getHasPin():
            return """The room has been protected by a pin number"""
        else:
            return """The room is not protected by a pin number"""


class VidyoOwnerRemovedNotification(VidyoOwnerNotificationBase):
    """ Template to build an email to the previous owner of a room
    """

    def __init__(self, booking, oldOwner):
        VidyoOwnerNotificationBase.__init__(self)
        self._owner = oldOwner
        self.setFromAddr("Indico Mailer <%s>" % Config.getInstance().getSupportEmail())
        self.setContentType("text/html")

        event = booking.getConference()

        self.setToList([oldOwner.getEmail()])

        self.setSubject("""[Indico] You are no longer the owner of a Vidyo public room attached to the event: %s""" % event.getTitle() )

        self.setBody("""Dear %s%s,<br />
<br />
This is an automatic email to inform you that you are no longer the owner of the Vidyo room with name "%s" in the event <a href="%s">%s</a>. The new owner is %s.<br />
<br />
Thank you for using our system.<br />
""" %
                     (self._getOwnerTitleText(),
                      oldOwner.getStraightFullName(),
                      booking.getBookingParamByName("roomName"),
                      urlHandlers.UHConferenceDisplay.getURL(event),
                      event.getTitle(),
                      booking.getOwner()["name"]))


class VidyoRoomDeletedOwnerNotification(VidyoOwnerNotificationBase):
    """ Template to build an email to the previous owner of a room
    """

    def __init__(self, booking):
        VidyoOwnerNotificationBase.__init__(self)
        self._owner = booking.getOwnerObject()

        self.setFromAddr("Indico Mailer <%s>" % Config.getInstance().getSupportEmail())
        self.setContentType("text/html")

        owner = booking.getOwnerObject()
        event = booking.getConference()

        self.setToList([owner.getEmail()])

        self.setSubject("""[Indico] The Vidyo public room %s has been deleted""" % booking.getBookingParamByName("roomName") )

        self.setBody("""Dear %s%s,<br />
<br />
Please note that the Vidyo room named "%s" associated with the Indico event <a href="%s">%s</a>, of which you were the owner, has been deleted by a manager of this event.<br />
<br />
Thank you for using Vidyo and Indico<br />
"""%
                     (self._getOwnerTitleText(),
                      owner.getStraightFullName(),
                      booking.getBookingParamByName("roomName"),
                      urlHandlers.UHConferenceDisplay.getURL(event),
                      event.getTitle()))
