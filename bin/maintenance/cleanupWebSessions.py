# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

from MaKaC.common import DBMgr
from MaKaC.webinterface.session.sessionManagement import getSessionManager

def deleteSessions(sm, todelete):
    done = 0
    for key in todelete:
        sm.delete_session(key)
        done += 1
    try:
        DBMgr.getInstance().commit()
    except:
        DBMgr.getInstance().sync()
    print "deleted %s of %s sessions" % (done, len(todelete))

DBMgr.getInstance().startRequest()
websessionDelay = float(24 * 3600)
sm = getSessionManager()
print "ok got session manager"
keys = sm.keys()
print "ok got keys"
done = 0
fresh = 0
todelete = []
batchsize = 1000

print "start deleting"
for key in keys:
    value = sm[key]
    try:
        if value.get_creation_age() > websessionDelay:
            todelete.append(key)
        else:
            fresh += 1
            if (fresh % batchsize) == 0:
                print "%s sessions too fresh to delete" % (fresh)
    except:
        print "cannot delete %s" % key
    if len(todelete) >= batchsize:
        deleteSessions(sm, todelete)
        todelete = []

if len(todelete) > 0:
    deleteSessions(sm, todelete)

print "%s sessions too fresh to delete" % (fresh)


DBMgr.getInstance().endRequest()
