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

"""
Service handlers for livesync management
"""

from indico.ext.livesync import SyncManager

# indico legacy imports
from MaKaC.services.implementation.base import AdminService, ParameterManager, \
     ServiceError
from MaKaC.plugins.base import Observable



# JSON Services

class AgentTypeInspector(Observable):
    """
    Just goes through agent types and catalogues them
    """

    @classmethod
    def getAvailableTypes(cls):
        types = {}
        cls()._notify('providesLiveSyncAgentType', types)
        return types

class AddAgent(AdminService):

    def _checkParams(self):
        pm = ParameterManager(self._params)

        self._type = pm.extract('type', pType=str)
        self._id = pm.extract('id', pType=str)
        self._name = pm.extract('name', pType=str)
        self._description = pm.extract('description', pType=str)
        self._specificParams = self._params['specific']

    def _getAnswer(self):
        sm = SyncManager.getDBInstance()

        avtypes = AgentTypeInspector.getAvailableTypes()

        if self._type not in avtypes:
            raise ServiceError('', 'Agent type %s is unknown' % self._type)

        typeClass = avtypes[self._type]
        sm.registerNewAgent(typeClass(self._id, self._name, self._description,
                                      60, **self._specificParams))

methodMap = {
    "livesync.addAgent": AddAgent

}

