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

from indico.core.db import DBMgr
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
        x = og.confToXML(conf, 1, 1, 1, overrideCache=True)
        y = og.confToXMLMarc21(conf, 1, 1, 1, overrideCache=True)
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

