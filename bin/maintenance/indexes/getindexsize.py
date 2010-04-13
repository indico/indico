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

from MaKaC.common.general import *
from MaKaC.common import db
from MaKaC.conference import CategoryManager
from MaKaC.common import indexes

def main():
    db.DBMgr.getInstance().startRequest()
    im = indexes.IndexesHolder()
    emailindex = im.getIndex('email')
    nameindex = im.getIndex('name')
    surnameindex = im.getIndex('surname')
    organisationindex = im.getIndex('organisation')
    calendarindex = im.getIndex('calendar')
    categindex = im.getIndex('category')
    print """
calendar:     %s
category:     %s
email:        %s
name:         %s
surname:      %s
organisation: %s""" % (len(repr(calendarindex.dump())),len(repr(categindex.dump())),len(repr(emailindex.dump())),len(repr(nameindex.dump())),len(repr(surnameindex.dump())),len(repr(organisationindex.dump())))
    db.DBMgr.getInstance().endRequest(False)

if __name__ == "__main__":
    main()
