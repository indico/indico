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
from MaKaC.user import AvatarHolder, Avatar, GroupHolder
from MaKaC.conference import CategoryManager, ConferenceHolder

ch = ConferenceHolder()
ah = AvatarHolder()
gh = GroupHolder()

print "Cleaning index..."
userIds = []

DBMgr.getInstance().startRequest()

for av in ah.getList():
    userIds.append(av.getId())

DBMgr.getInstance().endRequest()

i = 0
total = len(userIds)
for id in userIds:
    print "processed %d users on %d"%(i, total)
    i += 1
    DBMgr.getInstance().startRequest()
    av = ah.getById(id)
    av.resetLinkedTo()
    DBMgr.getInstance().endRequest()

print "Indexing groups..."
DBMgr.getInstance().startRequest()
for group in gh.getValuesToList():
    for prin in group.getMemberList():
        if isinstance(prin, Avatar):
            prin.linkTo(group, "member")
DBMgr.getInstance().endRequest()




def indexCategory(cat):
    for prin in cat.getConferenceCreatorList():
        if isinstance(prin, Avatar):
            prin.linkTo(cat, "creator")

    for prin in cat.getManagerList():
        if isinstance(prin, Avatar):
            prin.linkTo(cat, "manager")

    for prin in cat.getAllowedToAccessList():
        if isinstance(prin, Avatar):
            prin.linkTo(cat, "access")

    for c in cat.getSubCategoryList():
        indexCategory(c)

DBMgr.getInstance().startRequest()
root = CategoryManager().getRoot()
print "indexing categories..."
indexCategory(root)
DBMgr.getInstance().endRequest()


DBMgr.getInstance().startRequest()
confids = []
for conf in ch.getList():
    confids.append(conf.getId())
DBMgr.getInstance().endRequest()


print "indexing conferences..."

i = 0
total = len(confids)
for confId in confids:
    print "processed %d(current:%s) conferences on %d"%(i, confId, total)
    i += 1
    DBMgr.getInstance().startRequest()
    conf = ch.getById(confId)
    conf.getCreator().linkTo(conf, "creator")

    for prin in conf.getChairList():
        if isinstance(prin, Avatar):
            prin.linkTo(conf, "chair")

    for prin in conf.getManagerList():
        if isinstance(prin, Avatar):
            prin.linkTo(conf, "manager")

    for prin in conf.getAllowedToAccessList():
        if isinstance(prin, Avatar):
            prin.linkTo(conf, "access")

    for av in conf.getAbstractMgr().getAuthorizedSubmitterList():
        if isinstance(av, Avatar):
            av.linkTo(conf, "abstractSubmitter")

    for track in conf.getTrackList():
        for prin in track.getCoordinatorList():
            if isinstance(prin, Avatar):
                prin.linkTo(track, "coordinator")

    for al in conf.getAlarmList():
        for prin in al.getToUserList():
            if isinstance(prin, Avatar):
                prin.linkTo(al, "to")

    #sessions of the conference
    for ses in conf.getSessionList():
        for prin in ses.getManagerList():
            if isinstance(prin, Avatar):
                prin.linkTo(ses, "manager")

        for prin in ses.getAllowedToAccessList():
            if isinstance(prin, Avatar):
                prin.linkTo(ses, "access")

        for prin in ses.getCoordinatorList():
            if isinstance(prin, Avatar):
                prin.linkTo(ses, "coordinator")

        for mat in ses.getAllMaterialList():
            for prin in mat.getAllowedToAccessList():
                if isinstance(prin, Avatar):
                    prin.linkTo(mat, "access")


    #contributions of the conference
    for cont in conf.getContributionList():

        for prin in cont.getManagerList():
            if isinstance(prin, Avatar):
                prin.linkTo(cont, "manager")

        for prin in cont.getAllowedToAccessList():
            if isinstance(prin, Avatar):
                prin.linkTo(cont, "access")

        for mat in cont.getAllMaterialList():
            for prin in mat.getAllowedToAccessList():
                if isinstance(prin, Avatar):
                    prin.linkTo(mat, "access")

    #abstracts
    for abs in conf.getAbstractMgr().getAbstractList():

        if isinstance(abs.getSubmitter().getUser(), Avatar):
            abs.getSubmitter().getUser().linkTo(abs, "submitter")

    DBMgr.getInstance().endRequest()




