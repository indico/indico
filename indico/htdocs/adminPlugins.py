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
    return admins.RHAdminPlugins( req ).process( params )

def saveOptionReloadAll( req, **params ):
    return admins.RHAdminPluginsSaveOptionReloadAll( req ).process( params )

def reloadAll( req, **params ):
    return admins.RHAdminPluginsReloadAll( req ).process( params )

def clearAllInfo( req, **params ):
    return admins.RHAdminPluginsClearAllInfo( req ).process( params )

def savePluginTypeOptions( req, **params ):
    return admins.RHAdminPluginsSaveTypeOptions( req ).process( params )

def savePluginOptions( req, **params ):
    return admins.RHAdminPluginsSaveOptions( req ).process( params )

def reload( req, **params ):
    return admins.RHAdminPluginsReload( req ).process( params )

def toggleActivePluginType( req, **params ):
    return admins.RHAdminTogglePluginType( req ).process( params )

def toggleActive( req, **params ):
    return admins.RHAdminTogglePlugin( req ).process( params )