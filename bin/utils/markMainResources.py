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
n = 0
for contrib in conf.getContributionList():
    print "contrib: %s"%contrib.getId()
    paper = contrib.getPaper()
    if paper is not None:
        marked = False
        pdfRes = []
        for res in paper.getResourceList():
            if res.getFileType().strip().lower() == "pdf":
                pdfRes.append(res)
            if res.getName().strip().lower() == "main":
                paper.setMainResource(res)
                n += 1
                marked = True
                break
        if not marked and len(pdfRes) == 1:
            paper.setMainResource(pdfRes[0])
            n += 1
        elif maked:
            print "\t\t\t--->Already marked"
        elif len(pdfRes) > 1:
            print "\t\t\t--->More than one PDF"
        elif len(pdfRes) == 0:
            print "\t\t\t--->No PDF files"



print "%s resources were marked"%n

if not error:
    DBMgr.getInstance().endRequest()
    print "No error. The change are saved"
else:
    print "There were errors. The changes was not saved"



