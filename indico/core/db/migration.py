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

from ZODB.DB import DB

globalname_dict = {
    "PersistentMapping": ("persistent.mapping", None),
    "PersistentList": ("persistent.list", None),
    "CERNGroup": ("MaKaC.authentication.LDAPAuthentication", "LDAPGroup")
}

modulename_dict = {
    "IndexedCatalog.BTrees.": "BTrees.",
    "MaKaC.plugins.EPayment.CERNYellowPay.": "indico.ext.epayment.cern."
}


class MigratedDB(DB):
    """Subclass of ZODB.DB necessary to remove possible existing dependencies
        from IC"""

    def classFactory(self, connection, modulename, globalname):
        if globalname in globalname_dict:
            modulename = globalname_dict[globalname][0]
            if globalname_dict[globalname][1]:
                globalname = globalname_dict[globalname][1]
        for mod_name in modulename_dict:
            if mod_name[-1] == ".":
                if modulename.startswith(mod_name):
                    modulename = modulename_dict[mod_name] + modulename[len(mod_name):]
            elif modulename == mod_name:
                modulename = modulename_dict[modulename]
        return DB.classFactory(self, connection, modulename, globalname)
