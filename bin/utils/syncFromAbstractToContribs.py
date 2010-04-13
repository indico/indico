# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
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

from MaKaC.common import DBMgr
from MaKaC.conference import ConferenceHolder, ContributionParticipation
from MaKaC.review import AbstractStatusAccepted

conferenceId=""

DBMgr.getInstance().startRequest()
conf=ConferenceHolder().getById(conferenceId)
counter=[]
if conf is None:
    print "Error fetching conference"
else:
    for abstract in conf.getAbstractMgr().getAbstractList():
        if isinstance(abstract.getCurrentStatus(), AbstractStatusAccepted):
            contrib=abstract.getContribution()
            contrib.setTitle( abstract.getTitle() )
            contrib.setDescription( abstract.getContent() )
            contrib.setSummary( abstract.getSummary() )
            contrib.setTrack( abstract.getCurrentStatus().getTrack() )
            contrib.setType( abstract.getCurrentStatus().getType() )
            for auth1 in contrib.getPrimaryAuthorList()[:]:
                contrib.removePrimaryAuthor(auth1)
            for auth2 in contrib.getCoAuthorList()[:]:
                contrib.removeCoAuthor(auth2)
            for auth3 in contrib.getSpeakerList()[:]:
                contrib.removeSpeaker(auth3)
            for auth in abstract.getAuthorList():
                c_auth = ContributionParticipation()
                contrib._setAuthorValuesFromAbstract( c_auth, auth )
                if abstract.isPrimaryAuthor( auth ):
                    contrib.addPrimaryAuthor( c_auth )
                else:
                    contrib.addCoAuthor( c_auth )
                if abstract.isSpeaker( auth ):
                    contrib.addSpeaker( c_auth )
            # TODO: remove the previous submitter...how???
            contrib._grantSubmission(contrib.getAbstract().getSubmitter().getUser())
            counter.append(contrib.getId())
DBMgr.getInstance().endRequest()
print "contribs ids:%s"%counter
print ""
print "%s contribs sync"%(len(counter))

