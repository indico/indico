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

from MaKaC.user import AvatarHolder,GroupHolder
from MaKaC.domain import DomainHolder
from MaKaC.conference import ConferenceHolder


def migrateGroups(catalog):
    print "Migrating groups...",
    gh=GroupHolder()
    count=0
    for g in catalog.dump():
        gh._getIdx()[g.getId()]=g
        count+=1
    print "[Done:%s]"%count


def migrateAvatars(catalog):
    print "Migrating avatars...",
    ah=AvatarHolder()
    count=0
    for av in catalog.dump():
        ah._getIdx()[av.getId()]=av
        count+=1
    print "[Done:%s]"%count


def migrateDomains(catalog):
    print "Migrating domains...",
    dh=DomainHolder()
    count=0
    for dom in catalog.dump():
        dh._getIdx()[dom.getId()]=dom
        count+=1
    print "[Done:%s]"%count


def migrateConferences(catalog):
    print "Migrating Conferences...",
    ch=ConferenceHolder()
    count=0
    for conf in catalog.dump():
        ch._getIdx()[conf.getId()]=conf
        count+=1
    print "[Done:%s]"%count


from indico.core.db import DBMgr

DBMgr.getInstance().startRequest()
root=DBMgr.getInstance().getDBConnection().root()
migrateAvatars(root["Catalogs"]["MaKaC.user.Avatar"])
migrateGroups(root["Catalogs"]["MaKaC.user.Group"])
migrateDomains(root["Catalogs"]["MaKaC.domain.Domain"])
migrateConferences(root["Catalogs"]["MaKaC.conference.Conference"])
del root["Catalogs"]
del root["_ic_registry"]
del root["first time"]
from MaKaC.conference import CategoryManager
CategoryManager().getRoot()._reIndex()
DBMgr.getInstance().endRequest()
