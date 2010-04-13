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

import sys
sys.path.append("c:/development/indico/code/code")

from MaKaC.common import DBMgr
from MaKaC import conference



"""
It has been added a new attribute which is "mark as main resource" for
the material of a contribution. This script will mark [only for CHEP]
every resource with the name "main" or those we are the single pdfs in
the "paper" material.
"""

DBMgr.getInstance().startRequest()
error = False
ch = conference.ConferenceHolder()
conf = ch.getById("0")
print "conf %s"%conf.getTitle()
log = file('contribs_ids.txt','w')
lines = []
n = 0
for contrib in conf.getContributionList():
    paper = contrib.getPaper()
    if paper is not None:
        if paper.getMainResource() is not None:
            lines.append(contrib.getId())
log.writelines("\n".join(lines))
log.close()
if not error:
    DBMgr.getInstance().endRequest()
    print "No error. The change are saved"
else:
    print "There were errors. The changes was not saved"



