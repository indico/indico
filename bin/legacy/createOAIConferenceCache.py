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

from MaKaC.common import DBMgr
from MaKaC.conference import ConferenceHolder
from MaKaC.common.output import outputGenerator
from MaKaC.accessControl import AccessWrapper

def getConfIds():
    DBMgr.getInstance().startRequest()
    l = ConferenceHolder().getValuesToList()
    ids = []
    for conf in l:
        ids.append(conf.getId())

    DBMgr.getInstance().endRequest()
    return ids

def buildCache(ids):
    i = 1
    for id in ids:
        DBMgr.getInstance().startRequest()
        try:
            conf = ConferenceHolder().getById(id)
        except:
            print "conf %s not found"
            continue
        print i, ":", conf.getId()
        og = outputGenerator(AccessWrapper())
        x = og.confToXML(conf,1,1,1, forceCache=True)
        y = og.confToXMLMarc21(conf,1,1,1, forceCache=True)
        i += 1
        DBMgr.getInstance().endRequest()

usage = """USAGE: createOAIConferenceCahe.py [confId]"""

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print usage
    elif len(sys.argv) > 1:
        buildCache([sys.argv[1]])
    else:
        buildCache( getConfIds() )

