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
from MaKaC.webinterface.rh import conferenceModif
from MaKaC.webinterface import pages

from MaKaC.webinterface import pages

if DEVELOPMENT:
    pages = reload(pages)


def index(req, **params):
    p = pages.WPSessionCreation( req )
    params["postURL"] = "sessionCreation.py/create"
    return p.display( params )

def create(req, **args):
    p = pages.WPSessionCreation( req )
    p.createSession( args )
    return "done"

def convenerSearch( req, **params ):
    return conferenceModif.RHNewSessionConvenerSearch( req ).process( params )
    
def convenerNew( req, **params ):
    return conferenceModif.RHNewSessionConvenerNew( req ).process( params )
    
def personAdd( req, **params ):
    return conferenceModif.RHNewSessionPersonAdd( req ).process( params )
    