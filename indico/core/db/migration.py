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


class MigrationDB(DB):
    """Subclass of ZODB.DB necessary to remove possible existing dependencies
        from IC"""

    def classFactory(self, connection, modulename, globalname):
        if globalname == "PersistentMapping":
            modulename = "persistent.mapping"
        elif globalname == "PersistentList":
            modulename = "persistent.list"
        elif modulename.startswith("IndexedCatalog.BTrees."):
            modulename = "BTrees.%s" % modulename[22:]
        elif modulename.startswith("MaKaC.plugins.EPayment.CERNYellowPay."):
            modulename = "indico.ext.epayment.cern.%s" \
                % modulename[len("MaKaC.plugins.EPayment.CERNYellowPay."):]
        return DB.classFactory(self, connection, modulename, globalname)
