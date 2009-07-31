import MaKaC.conference

def prettyPrint(obj):
    if type(obj) == MaKaC.conference.DeletedObject:
        return "DeletedObject<%s>" % (obj.getId())
    elif type(obj) == MaKaC.conference.Conference:
        try:
            owner = obj.getOwner().id
        except:
            owner = 'ORPHAN'

        return "Conference< %s @ %s >" % (obj.getId(),owner)
    elif type(obj) == MaKaC.conference.Contribution:
        try:
            owner = obj.getConference().getId()
        except:
            owner = "ORPHAN"

        return "Contribution< %s @ %s >" % (obj.getId(),owner)
    elif type(obj) == MaKaC.conference.AcceptedContribution:
        try:
            owner = obj.getConference().getId()
        except:
            owner = "ORPHAN"

        return "AcceptedContribution< %s @ %s >" % (obj.getId(),owner)
    elif type(obj) == MaKaC.conference.SubContribution:
        try:
            owner = obj.getOwner().getId()
            conf = obj.getConference().getId()
        except:
            owner = "ORPHAN"
            conf = "ORPHAN"
        return "SubContribution< %s @ %s @ %s >" % (obj.getId(),owner,conf)
    else:
        return obj

def getParent(obj):
    if type(obj) == MaKaC.conference.Conference:
        try:
            return obj.getOwner()
        except:
            return None
    else:
        try:
            return obj.getConference()
        except:
            return None
