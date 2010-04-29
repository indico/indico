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

import MaKaC.webinterface.rh.admins as admins


def index( req, **params ):
    return admins.RHAdminArea( req ).process( params )

def switchCacheActive( req, **params ):
    return admins.RHAdminSwitchCacheActive( req ).process( params )

def switchDebugActive( req, **params ):
    return admins.RHAdminSwitchDebugActive( req ).process( params )

def switchNewsActive( req, **params ):
    return admins.RHAdminSwitchNewsActive( req ).process( params )

def switchHighlightActive( req, **params ):
    return admins.RHAdminSwitchHighlightActive( req ).process( params )

def selectAdmins( req, **params ):
    return admins.RHAdminSelectUsers( req ).process( params )

def addAdmins( req, **params ):
    return admins.RHAdminAddUsers( req ).process( params )
    
def removeAdmins( req, **params ):
    return admins.RHAdminRemoveUsers( req ).process( params )
    

