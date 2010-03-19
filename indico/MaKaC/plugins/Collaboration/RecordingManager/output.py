from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.user import Avatar
from MaKaC.user import CERNGroup

class MarcAccessListGenerator():
    def __init__(self):
        pass

    def generateAccessList(self, out, conf):
        # Only provide MARC tag 506 information if there is any access list
        # Get set containing Avatar objects (if empty, that means event is public)
        allowed_users = conf.getRecursiveAllowedToAccessList()
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

            # Get subfields from plugin settings:
            field506tag2 = CollaborationTools.getOptionValue("RecordingManager", "MarcField506Subfield2")
            field506tag5 = CollaborationTools.getOptionValue("RecordingManager", "MarcField506Subfield5")

            # Create section for tag 506, listing allowed groups
            if len(allowed_groups) > 0:
                out.openTag("marc:datafield",[["tag","506"], ["ind1","1"], ["ind2"," "]])
                out.writeTag("marc:subfield", "Restricted",  [["code", "a"]])
                for group_id in allowed_groups:
                    out.writeTag("marc:subfield", group_id,  [["code", "d"]])
                out.writeTag("marc:subfield", "group",       [["code", "f"]])
                out.writeTag("marc:subfield", field506tag2, [["code", "2"]])
                out.writeTag("marc:subfield", field506tag5, [["code", "5"]])
                out.closeTag("marc:datafield")

            # Create another section for tag 506, listing allowed users
            if len(allowed_users) > 0:
                out.openTag("marc:datafield",[["tag","506"], ["ind1","1"], ["ind2"," "]])
                out.writeTag("marc:subfield", "Restricted",  [["code", "a"]])
                for email_id in allowed_emails:
                    out.writeTag("marc:subfield", email_id,  [["code", "d"]])
                out.writeTag("marc:subfield", "email",       [["code", "f"]])
                out.writeTag("marc:subfield", field506tag2, [["code", "2"]])
                out.writeTag("marc:subfield", field506tag5, [["code", "5"]])
                out.closeTag("marc:datafield")
