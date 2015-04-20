# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

"""
We have two dictionaries

    - globalname_dict: We declare the classes that are going to be moved or renamed.
                       The key is the name to be renamed or moved.
                       The value is a tuple with the new module name and the new class; it can have only one value
                       or both.
    - modulename_dict: We declare the modules that are going to be moved.
                       The key is the old module's name and if it finishes with '.' means that
                       that module and all submodules are going to be moved.
                       The value is the new module and also follows the same rules as the key.
"""

globalname_dict = {
    "PersistentMapping": ("persistent.mapping", None),
    "PersistentList": ("persistent.list", None),
    "LDAPGroup": ("MaKaC.authentication.LDAPAuthentication", None),
    "CERNGroup": ("MaKaC.authentication.LDAPAuthentication", "LDAPGroup"),
    "PeriodicTask": ("indico.modules.scheduler.tasks.periodic", None),
    "PeriodicUniqueTask": ("indico.modules.scheduler.tasks.periodic", None),
    "TaskOccurrence": ("indico.modules.scheduler.tasks.periodic", None),
    "CategoryStatisticsUpdaterTask": ("indico.modules.scheduler.tasks.periodic", None),
    "FoundationSyncTask": ("indico.modules.scheduler.tasks.periodic", None),
    "SamplePeriodicTask": ("indico.modules.scheduler.tasks.periodic", None)
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
            if globalname_dict[globalname][0]:
                modulename = globalname_dict[globalname][0]
            if globalname_dict[globalname][1]:
                globalname = globalname_dict[globalname][1]
        # There is an else in order to do not overwrite the rule.
        # It could create some inconsistency
        elif modulename in modulename_dict:
            modulename = modulename_dict[modulename]
        else:
            # This is the case of a module with submodules
            for former_mod_name in modulename_dict:
                if former_mod_name[-1] == "." and modulename.startswith(former_mod_name):
                        modulename = modulename_dict[former_mod_name] + modulename[len(former_mod_name):]
        return DB.classFactory(self, connection, modulename, globalname)
