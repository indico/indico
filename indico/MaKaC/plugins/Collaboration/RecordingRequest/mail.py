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
from MaKaC.plugins.Collaboration.RecordingRequest.common import typeOfEvents, \
    postingUrgency, recordingPurpose, intendedAudience, subjectMatter, lectureOptions, \
    getTalks


class RecordingRequestNotificationBase(GenericNotification):
    """ Base class to build an email notification for the Recording request plugin.
    """
    def __init__(self, booking):
        GenericNotification.__init__(self)

        self._booking = booking
        self._bp = booking._bookingParams
        self._conference = booking.getConference()
        self._isLecture = self._conference.getType() == 'simple_event'

        self._modifLink = str(booking.getModificationURL())

        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
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
            <strong>Talk(s) to be recorded:</strong>
        </td>
        <td style="vertical-align: top;">
            %s
        </td>
    </tr>
    <tr>
        <td colspan="2">
            <strong>Comments about talk selection</strong><br />
            %s
        </td>
    </tr>
    <tr>
        <td colspan="2">
            <strong>Have all the speakers given permission to have their talks recorded?</strong>  %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Lecture options:</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Type of event:</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Posting urgency:</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Number of remote viewers:</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Number of attendees:</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Recording purpose(s):</strong>
        </td>
        <td style="vertical-align: top">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Intended audience(s):</strong>
        </td>
        <td style="vertical-align: top; white-space : nowrap;">
            %s
        </td>
    </tr>
    <tr>
        <td style="vertical-align: top; white-space : nowrap;">
            <strong>Subject matter(s):</strong>
        </td>
        <td style="vertical-align: top">
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
            <strong>List of talks to be recorded:</strong>
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
       self._getTalkSelectionComments(),
       bp["permission"],
       dict(lectureOptions)[bp["lectureOptions"]],
       dict(typeOfEvents)[bp['lectureStyle']],
       dict(postingUrgency)[bp['postingUrgency']],
       str(bp['numRemoteViewers']),
       str(bp['numAttendees']),
       self._getPurposes(),
       self._getAudiences(),
       self._getMatters(),
       self._getComments(),
       self._getTalks())

    def _getTalks(self):
        if self._isLecture:
            return """(This event is a lecture. Therefore, it has no talks)"""

        else:
            #"all" "choose" "neither"
            if self._bp["talks"] == "all":
                text = ["""The user chose "All Talks". List of talks:"""]
                allTalks = getTalks(self._conference)
                if allTalks:
                    text.extend(MailTools.talkListText(self._conference, allTalks))
                    text.append("<strong>Important note:</strong> room is only shown if different from event.")
                else:
                    text.append("(This event has no talks)")
                return "<br />".join(text)

            elif self._bp["talks"] == "neither":
                return """Please see the talk selection comments"""

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
                return """The user chose "All Talks". The list of all talks can be found at the end of this e-mail."""
            elif self._bp["talks"] == "neither":
                return """Please see the talk selection comments"""
            else:
                return """The user chose "Choose talks". The list of chosen talks can be found at the end of this e-mail."""

    def _getTalkSelectionComments(self):
        if self._isLecture:
            return """(This event is a lecture. Therefore, it has no talk selection comments)"""
        else:
            comments = None
            if self._bp["talkSelectionComments"]:
                comments = self._bp["talkSelectionComments"].strip()
            if comments:
                return comments
            return "(User didn't write any comments)"

    def _getComments(self):
        comments = self._bp["otherComments"].strip()
        if comments:
            return comments
        return "(User didn't write any comments)"

    def _getLectureOptions(self):
        options = self._bp['lectureOptions']
        lodict = dict(lectureOptions)
        if options:
            return MailTools.listToStr([lodict[k] for k in options])
        else:
            return "No lecture options were selected"

    def _getPurposes(self):
        purposes = self._bp['recordingPurpose']
        rpdict = dict(recordingPurpose)
        if purposes:
            return MailTools.listToStr([rpdict[k] for k in purposes])
        else:
            return "No purposes were selected"

    def _getAudiences(self):
        audiences = self._bp['intendedAudience']
        iadict = dict(intendedAudience)
        if audiences:
            return MailTools.listToStr([iadict[k] for k in audiences])
        else:
            return "No audiences were selected"

    def _getMatters(self):
        matters = self._bp['subjectMatter']
        smdict = dict(subjectMatter)
        if matters:
            return MailTools.listToStr([smdict[k] for k in matters])
        else:
            return "No audiences were selected"



class RecordingRequestAdminNotificationBase(RecordingRequestNotificationBase):
    """ Base class to build an email notification to Admins
    """
    def __init__(self, booking):
        RecordingRequestNotificationBase.__init__(self, booking)
        self.setToList(MailTools.getAdminEmailList('RecordingRequest'))


class RecordingRequestManagerNotificationBase(RecordingRequestNotificationBase):
    """ Base class to build an email notification to Users
    """
    def __init__(self, booking):
        RecordingRequestNotificationBase.__init__(self, booking)
        self.setToList(MailTools.getManagersEmailList(self._conference, 'RecordingRequest'))


class NewRequestNotification(RecordingRequestAdminNotificationBase):
    """ Template to build an email notification to the recording responsible
    """

    def __init__(self, booking):
        RecordingRequestAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[RecReq] New recording request: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Recording Responsible,<br />
<br />
There is a <strong>new recording request</strong> in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to accept or reject the request.<br />
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
        MailTools.organizerDetails(self._conference),
        MailTools.eventDetails(self._conference),
        self._getRequestDetails('new')
        ))



class RequestModifiedNotification(RecordingRequestAdminNotificationBase):
    """ Template to build an email notification to the recording responsible
    """

    def __init__(self, booking):
        RecordingRequestAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[RecReq] Recording request modified: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Recording Responsible,<br />
<br />
A recording request <strong>has been modified</strong> in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to accept or reject the request.<br />
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
        self._getRequestDetails('modify')
        ))



class RequestDeletedNotification(RecordingRequestAdminNotificationBase):
    """ Template to build an email notification to the recording responsible
    """

    def __init__(self, booking):
        RecordingRequestAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[RecReq] Recording request withdrawn: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Recording Responsible,<br />
<br />
A recording request <strong>has been withdrawn</strong> in <a href="%s">%s</a><br />
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

class RequestAcceptedNotification(RecordingRequestManagerNotificationBase):
    """ Template to build an email notification to the event managers
        when a request gets accepted.
    """

    def __init__(self, booking):
        RecordingRequestManagerNotificationBase.__init__(self, booking)

        self.setSubject("""[Indico] Recording request accepted: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Event Manager,<br />
<br />
Your recording request for the event: "%s" has been accepted.<br />
Click <a href="%s">here</a> to view your request.<br />
<br />
Best Regards,<br />
Recording Responsibles

""" % ( self._conference.getTitle(),
        self._modifLink
      ))

class RequestAcceptedNotificationAdmin(RecordingRequestAdminNotificationBase):
    """ Template to build an email notification to the admins when a request gets accepted
    """

    def __init__(self, booking):
        RecordingRequestAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[RecReq] Recording request accepted: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Recording Responsible,<br />
<br />
A recording request for the event: "%s" has been accepted in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to view the request.<br />

""" % ( self._conference.getTitle(),
        MailTools.getServerName(),
        MailTools.getServerName(),
        self._modifLink
      ))


class RequestRejectedNotification(RecordingRequestManagerNotificationBase):
    """ Template to build an email notification to the event managers
        when a request gets accepted.
    """


    def __init__(self, booking):

        RecordingRequestManagerNotificationBase.__init__(self, booking)

        self.setSubject("""[Indico] Recording request rejected: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))
        self.setBody("""Dear Event Manager,<br /><br />
The recording request for the event: "%s" has been rejected.<br />
Click <a href="%s">here</a> to view your request.<br />
<br />
The reason given by the Recording responsible was:
<br />
%s
<br />
<br />
Best Regards,<br />
Recording Responsibles
""" % ( self._conference.getTitle(),
        self._modifLink,
        self._booking.getRejectReason().strip()
        ))

class RequestRejectedNotificationAdmin(RecordingRequestAdminNotificationBase):
    """ Template to build an email notification to the admins when a request gets accepted
    """

    def __init__(self, booking):
        RecordingRequestAdminNotificationBase.__init__(self, booking)

        self.setSubject("""[RecReq] Recording request rejected: %s (event id: %s)"""
                        % (self._conference.getTitle(), str(self._conference.getId())))

        self.setBody("""Dear Recording Responsible,<br />
<br />
A recording request for the event: "%s" has been rejected in <a href="%s">%s</a><br />
Click <a href="%s">here</a> to view the request.<br />
<br />
The reason given by the Webcast Responsible who rejected the request was:
<br />
%s
<br />

""" % ( self._conference.getTitle(),
        MailTools.getServerName(),
        MailTools.getServerName(),
        self._modifLink,
        self._booking.getRejectReason().strip()
      ))
