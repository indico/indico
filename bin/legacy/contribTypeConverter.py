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

import sys
sys.path.append("c:/development/indico/code/code")

from indico.core.db import DBMgr
from MaKaC import conference
from MaKaC import review



"""
The contribution type was set in the call for abstract part as a string.
Now we moved it at the conference level using contribType objects.
To convert the contribution type of the abstract which are already submitted,
we use the name attribut of the contribType object.
So, before running this script, you must create contribType objects with
setting the name equal to the old contribution type string.
"""

DBMgr.getInstance().startRequest()
error = False
ch = conference.ConferenceHolder()
for conf in ch.getList():
    print "conf number %s"%conf.getId()
    #build a dic with old type as key and new type as value
    oldTypes = conf.getAbstractMgr().getContribTypeList()
    newTypes = conf.getContribTypeList()
    typeDic = {}
    for oldType in oldTypes:
        typeDic[oldType] = None
        found = False
        for newType in newTypes:
            if newType.getName().lower().strip() == oldType.lower().strip():
                typeDic[oldType] = newType
                found = True
        if not found:
            newType = conference.ContributionType(oldType, '', conf)
            conf.addContribType(newType)
            typeDic[oldType] = newType

    for k in typeDic.keys():
        name = None
        if typeDic[k]:
            name = typeDic[k].getName()
        print "%s: %s"%(k, name)

    #convert the abstract contribution type
    for abstract in conf.getAbstractMgr().getAbstractList():
        for jud in abstract.getTrackAcceptanceList():
            if jud.getContribType()=="" or jud.getContribType()==None:
                jud._contribType=None
            elif jud.getContribType() in typeDic.keys():
                jud._contribType=typeDic[jud.getContribType()]
            else:
                print "confId:%s abstractId:%s  -  This abstract have a jugdment 'propose to accept'"%(conf.getId(), abstract.getId())
                error = True
        status=abstract.getCurrentStatus()
        if isinstance(status,review.AbstractStatusAccepted):
            if status.getType()=="" or status.getType()==None:
                status._setType(None)
            elif status.getType() in typeDic.keys():
                status._setType(typeDic[status.getType()])
            else:
                print "confId:%s abstractId:%s  -  This abstract have a jugdment 'propose to accept'"%(conf.getId(), abstract.getId())
                error = True
                break
        if not abstract.getContribType():
            abstract.setContribType(None)
        elif abstract.getContribType() in typeDic.keys():
            if typeDic[abstract.getContribType()]:
                abstract.setContribType(typeDic[abstract.getContribType()])
            else:
                print "confId:%s abstractId:%s  -  no contribType found to convert the contribution type"%(conf.getId(), abstract.getId())
                error = True
        else:
            print "confId:%s abstractId:%s  -  The contribution type is not set in the CFA manager"%(conf.getId(), abstract.getId())
            error = True
    #convert the template conditions contrib type
    for tpl in conf.getAbstractMgr().getNotificationTplList():
        for cond in tpl.getConditionList():
            if isinstance(cond,review.NotifTplCondAccepted):
                oldType=cond.getContribType()
                if oldType is None or oldType=="" or oldType=="--any--":
                    continue
                cond._contribType=typeDic[oldType]

if not error:
    DBMgr.getInstance().endRequest()
    print "No error. The change are saved"
else:
    print "There were errors. The changes was not saved"



