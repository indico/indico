from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.user import Avatar
from MaKaC.user import CERNGroup

from MaKaC.common.logger import Logger

class MarcAccessListGenerator():
    def __init__(self):
        pass

    def generateAccessListXML(self, out, obj):
        """Generate a comprehensive access list showing all users and e-groups who may access
        this object, taking into account the permissions and access lists of its owners.
        obj could be a Conference, Session, Contribution, or SubContribution object."""

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

    def generateVideoXML(self, out, recordingManagerTags):
        """Generate XML variables needed for video records."""

        Logger.get('RecMan').info("in generateVideoXML(), contentType = %s" % recordingManagerTags["contentType"])
        Logger.get('RecMan').info("in generateVideoXML(), contentType = %s" % recordingManagerTags["videoFormat"])

        # retrieve actual syntax to use from RecordingManager plug-in options.
        videoTagStandard      = CollaborationTools.getOptionValue("RecordingManager", "videoFormatStandard")
        videoTagWide          = CollaborationTools.getOptionValue("RecordingManager", "videoFormatWide")
        contentTypeWebLecture = CollaborationTools.getOptionValue("RecordingManager", "contentTypeWebLecture")

        # If it's plain video, specify whether standard or wide format
        if recordingManagerTags["contentType"] == 'plain_video':
            if recordingManagerTags["videoFormat"] == 'standard':
                out.writeTag("videoFormat", videoTagStandard)
            elif recordingManagerTags["videoFormat"] == 'wide':
                out.writeTag("videoFormat", videoTagWide)
        # if it's a web lecture, then specify that.
        elif recordingManagerTags["contentType"] == 'web_lecture':
            out.writeTag("videoFormat", contentTypeWebLecture)

    def generateLanguagesXML(self, out, recordingManagerTags):
        """Generate XML variables needed for language information."""

        if len(recordingManagerTags["languages"]) > 0:
            out.openTag("languages")
            for l in recordingManagerTags["languages"]:
                Logger.get('RecMan').info("in generateLanguagesXML(), language = %s" % l)
                out.writeTag("code", l)
            out.closeTag("languages")
