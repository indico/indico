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



