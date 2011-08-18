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

