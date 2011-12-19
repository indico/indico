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
from MaKaC.user import AvatarHolder
from MaKaC.conference import ConferenceHolder
from MaKaC.review import AbstractStatusSubmitted

"""
Propose  to be accepted the abstracts with status submitted of a track
"""

DBMgr.getInstance().startRequest()
error = False

confId = '149557'
trackId = '3'
userId = '27108'
contribTypeId = '2'

conf = ConferenceHolder().getById(confId)
track = conf.getTrackById(trackId)
contribType = conf.getContribTypeById(contribTypeId)
user = AvatarHolder().getById(userId)

for abstract in track.getAbstractList():
    if isinstance(abstract.getCurrentStatus(), AbstractStatusSubmitted):
        abstract.proposeToAccept(user, track, contribType)

if not error:
    DBMgr.getInstance().endRequest()
    print "No error. The change are saved"
else:
    print "There were errors. The changes was not saved"