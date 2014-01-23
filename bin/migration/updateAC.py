# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
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

from indico.core.db import DBMgr
from MaKaC.conference import CategoryManager, ConferenceHolder


DBMgr.getInstance().startRequest()
for cat in CategoryManager().getList():
    cat.getAccessController().setOwner(cat)

DBMgr.getInstance().endRequest()

def setConference(conf):
    conf.getAccessController().setOwner(conf)
    for mat in conf.getAllMaterialList():
        setMaterial(mat)
    for session in conf.getSessionList():
        setSession(session)
    for cont in conf.getContributionList():
        setContribution(cont)


def setSession(session):
    session.getAccessController().setOwner(session)
    for mat in session.getAllMaterialList():
        setMaterial(mat)

def setContribution(cont):
    cont.getAccessController().setOwner(cont)
    for mat in cont.getAllMaterialList():
        setMaterial(mat)

def setMaterial(mat):
    mat.getAccessController().setOwner(mat)
    for res in mat.getResourceList():
        setResource(res)

def setResource(res):
    res.getAccessController().setOwner(res)



DBMgr.getInstance().startRequest()

confIds = []
for conf in ConferenceHolder().getList():
    confIds.append(conf.getId())

DBMgr.getInstance().endRequest()

ch = ConferenceHolder()

for id in confIds:
    for i in range(10):
        try:
            DBMgr.getInstance().startRequest()
            setConference(ch.getById(id))
            DBMgr.getInstance().endRequest()
            break
        except Exception, e:
            DBMgr.getInstance().abort()
            print "try %d raise error: %s"%(i, e)

