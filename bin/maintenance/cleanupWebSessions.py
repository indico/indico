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

DBMgr.getInstance().startRequest()
websessionDelay = float(24 * 3600)
sm = getSessionManager()
print "ok got session manager"
keys = sm.keys()
print "ok got keys"
nbcommit = 100
done = 0
deleted = 0
todelete = []

print "set up list of keys to be deleted"
for key in keys:
  value = sm[key]
  try:
    if value.get_creation_age() > websessionDelay:
      todelete.append(key)
      deleted+=1
  except:
    print "cannot delete %s" % key
  done+=1

print "start deletion"
while len(todelete) > 0:
  batch = todelete[:100]
  todelete = todelete[100:]
  i = 0
  while i<10:
    for key in batch:
      sm.delete_session(key)
    try:
      DBMgr.getInstance().commit()
      break
    except:
      DBMgr.getInstance().sync()
      i += 1

print "deleted %s of %s sessions" % (deleted, done)

DBMgr.getInstance().endRequest()
