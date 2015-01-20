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

import sys,os,re

from MaKaC import user
from indico.core.db import DBMgr
import MaKaC.common.indexes as indexes


def main():
    """This script deletes existing user indexes (email,name,surname,organisation) and recreates them."""
    DBMgr.getInstance().startRequest()
    try:
      del DBMgr.getInstance().getDBConnection().root()['indexes']['email']
    except:
      pass
    try:
      del DBMgr.getInstance().getDBConnection().root()['indexes']['name']
    except:
      pass
    try:
      del DBMgr.getInstance().getDBConnection().root()['indexes']['surName']
    except:
      pass
    try:
      del DBMgr.getInstance().getDBConnection().root()['indexes']['organisation']
    except:
      pass
    try:
      del DBMgr.getInstance().getDBConnection().root()['indexes']['status']
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
    DBMgr.getInstance().endRequest()

if __name__ == "__main__":
    main()

