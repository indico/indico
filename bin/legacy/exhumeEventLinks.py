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
from MaKaC import user
from MaKaC import conference

import traceback

curper = -1
fixes = 0

def percent_show(fraction, total):
    global curper

    per = int(float(fraction)/float(total)*100)

    if per != curper:
        print "%d%% %d/%d" % (per, fraction, total)
        curper = per

def exhumeLinks(avatarHolder, conf):

    global fixes

    conf.getCreator().linkTo(conf, "creator")

    for participant in conf.getParticipation().getParticipantList():

        avatar = participant.getAvatar()

        if avatar:
            avatar.linkTo(conf, "participant")
            fixes += 1

    registrants = conf.getRegistrants()
    for regIdx in registrants:
        avatar = registrants[regIdx].getAvatar()

        if avatar:
            registrants[regIdx].getAvatar().linkTo(registrants[regIdx], "registrant")
            fixes += 1

    for manager in conf.getManagerList():

        if type(manager) == user.Avatar:
            manager.linkTo(conf, "manager")
            fixes += 1

try:
    DBMgr.getInstance().startRequest()

    ah = user.AvatarHolder()
    ch = conference.ConferenceHolder()
    list = ch.getList()

    totalConfs = len(list)

    print totalConfs,'registers'

    count = 0;

    for conf in ch.getList():
        count += 1
        percent_show(count, totalConfs);
        exhumeLinks(ah,conf)

        DBMgr.getInstance().commit()
        DBMgr.getInstance().sync()

    DBMgr.getInstance().endRequest()

    print "%d fixes done" % fixes

except Exception,e:
    print 'Exception:',e
    traceback.print_exc()
