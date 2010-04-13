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



# TODO: this file should be removed. I think it is not used anymore! (Jose B.)
from MaKaC.common.general import *

if DEVELOPMENT:
    from MaKaC import webinterface
    webinterface = reload( webinterface )

from MaKaC.webinterface import pages


def index( req, **params ):
    p = pages.WPConfModifMainData( req )
    return p.display( params )

def selectChairs(req, **args):
    p = pages.WPConferenceSelectChairs( req )
    return p.display( args )

def addChairs(req, **args):
    p = pages.WPConfModifMainData(req)
    str = p.addChairmans(args)
    return str

def removeChairs(req, **args):
    p = pages.WPConfModifMainData(req)
    str = p.removeChairmans(args)
    return str

def removeMaterials( req, **params ):
    p = pages.WPConfModifMainData(req)
    str = p.removeMaterials(params)
    return str



