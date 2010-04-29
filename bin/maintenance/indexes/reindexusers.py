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

import sys,os,re

sys.path.append("/home/jbenito/development/indico/code/code")

from MaKaC import user
from MaKaC.common.general import *
from MaKaC.common import db
import MaKaC.common.indexes as indexes


def main():
    """This script deletes existing user indexes (email,name,surname,organisation) and recreates them."""
    db.DBMgr.getInstance().startRequest()
    try:
      del db.DBMgr.getInstance().getDBConnection().root()['indexes']['email']
    except:
      pass
    try:
      del db.DBMgr.getInstance().getDBConnection().root()['indexes']['name']
    except:
      pass
    try:
      del db.DBMgr.getInstance().getDBConnection().root()['indexes']['surName']
    except:
      pass
    try:
      del db.DBMgr.getInstance().getDBConnection().root()['indexes']['organisation']
    except:
      pass
    try:
      del db.DBMgr.getInstance().getDBConnection().root()['indexes']['status']
    except:
      pass
    ah = user.AvatarHolder()
    ih = indexes.IndexesHolder()
    emailindex = ih.getById( 'email' )
    nameindex = ih.getById( 'name' )
    surNameindex = ih.getById( 'surName' )
    orgindex = ih.getById( 'organisation' )
    statindex = ih.getById( 'status' )
    users = ah.getList()
    for us in users:
    	emailindex.indexUser(us)
    	nameindex.indexUser(us)
    	surNameindex.indexUser(us)
    	orgindex.indexUser(us)
    	statindex.indexUser(us)
    db.DBMgr.getInstance().endRequest()

if __name__ == "__main__":
    main()

