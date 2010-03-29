from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.user import Avatar
from MaKaC.user import CERNGroup

from MaKaC.common.logger import Logger

class MarcAccessListGenerator():
    def __init__(self):
        pass

    def generateAccessListXML(self, out, obj):
        """obj could be a Conference, Session, Contribution, or SubContribution object."""

        allowed_users = obj.getRecursiveAllowedToAccessList()
        if allowed_users is not None and len(allowed_users) > 0:
            # Populate two lists holding email/group strings instead of Avatar/Group objects
            allowed_emails = []
            allowed_groups = []
            for user_obj in allowed_users:
                if isinstance(user_obj, Avatar):
                    allowed_emails.append(user_obj.getEmail())
                elif isinstance(user_obj, CERNGroup):
                    allowed_groups.append(user_obj.getId() + " [CERN]")
                else:
                    allowed_emails.append("UNKNOWN: %s" % user_obj.getId())

            # Create XML list of groups
            if len(allowed_groups) > 0:
                out.openTag("allowedAccessGroups")
                for group_id in allowed_groups:
                    out.writeTag("group", group_id)
                out.closeTag("allowedAccessGroups")

            # Create XML list of emails
            if len(allowed_users) > 0:
                out.openTag("allowedAccessEmails")
                for email_id in allowed_emails:
                    out.writeTag("email", email_id)
                out.closeTag("allowedAccessEmails")

    def generateVideoXML(self, out, obj, contentType, videoFormat):
        """Generate XML variables needed for video records."""

        Logger.get('RecMan').info("videoFormat = %s" % videoFormat)

        videoTagStandard      = CollaborationTools.getOptionValue("RecordingManager", "videoFormatStandard")
        videoTagWide          = CollaborationTools.getOptionValue("RecordingManager", "videoFormatWide")
        contentTypeWebLecture = CollaborationTools.getOptionValue("RecordingManager", "contentTypeWebLecture")

        Logger.get('RecMan').info("in generateVideoXML(), contentType = %s" % contentType)

        if contentType == 'plain_video':
            if videoFormat == 'standard':
                out.writeTag("videoFormat", videoTagStandard)
            elif videoFormat == 'wide':
                out.writeTag("videoFormat", videoTagWide)
        elif contentType == 'web_lecture':
            out.writeTag("videoFormat", contentTypeWebLecture)
