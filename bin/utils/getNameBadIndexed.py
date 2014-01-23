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
from MaKaC.common.indexes import IndexesHolder


"""
Generates a file with all the avatars that are not well indexed by name.
"""

DBMgr.getInstance().startRequest()
error = False
ah = user.AvatarHolder()
ni=IndexesHolder()._getIdx()["name"]
log = file('names_ids.txt','w')
lines = []
for uid, user in ah._getIdx().iteritems():
    for word in ni._words:
        if uid in ni._words[word] and word != user.getName():
            lines.append(uid + "-" + user.getName() + "-" + word)
log.writelines("\n".join(lines))
log.close()
if not error:
    DBMgr.getInstance().endRequest()
    print "No error. The change are saved"
else:
    print "There were errors. The changes was not saved"

