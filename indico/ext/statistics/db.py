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

from indico.ext.statistics.util import getPluginType

def updateDBStructure(root, storage_name=None, storage_type=None):

    if storage_name is None or storage_type is None:
        raise Exception("Cannot check nor instantiate with no storage name.")

    plugin_type = getPluginType()
    plugin_storage = plugin_type.getStorage()

    if storage_name in plugin_storage:
        raise Exception('The database already contains Indico Statistics')
    else:
        plugin_storage[storage_name] = storage_type()