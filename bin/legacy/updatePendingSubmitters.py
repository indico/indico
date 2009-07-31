from MaKaC.common import DBMgr
from MaKaC.conference import ConferenceHolder

CONFID='XXXXX'  # Replace XXXX with the ID of your conference.

DBMgr.getInstance().startRequest()

c=ConferenceHolder().getById(CONFID)

for contrib in c.getContributionList():
    contrib._submittersEmail=map(lambda x: x.lower(),contrib.getSubmitterEmailList())

DBMgr.getInstance().commit()
DBMgr.getInstance().sync()

for contrib in c.getContributionList():
    for email in contrib.getSubmitterEmailList():
        email=email.lower()
        res=AvatarHolder().match({'email':email})
        if len(res)==1:
            contrib.grantSubmission(res[0])
            contrib.revokeSubmissionEmail(email)

DBMgr.getInstance().commit()

DBMgr.getInstance().endRequest()

