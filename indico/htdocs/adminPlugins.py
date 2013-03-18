# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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