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



