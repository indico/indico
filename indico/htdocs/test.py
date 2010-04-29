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

from MaKaC.webinterface.wcomponents import WTemplated

class TestHeader(WTemplated):
    pass


class TestFooter(WTemplated):
    pass


class TestMenu(WTemplated):
    pass


class TestMain(WTemplated):

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["menu"]=TestMenu().getHTML()
        return vars


class TestPage(WTemplated):
    
    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["header"]=TestHeader().getHTML()
        vars["footer"]=TestFooter().getHTML()
        vars["main"]=TestMain().getHTML()
        return vars


def index(req, **params):
    return TestPage().getHTML()

