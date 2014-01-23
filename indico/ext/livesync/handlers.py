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

"""
Service handlers for livesync management
"""

# indico imports
from indico.util.date_time import nowutc, int_timestamp

# plugin imports
from indico.ext.livesync import SyncManager

# indico legacy imports
from MaKaC.services.implementation.base import AdminService, ParameterManager, \
     ServiceError
from MaKaC.plugins.base import Observable
from MaKaC.accessControl import AdminList


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


class AgentModificationService(AdminService):

    def _checkParams(self):
        self._pm = ParameterManager(self._params)

        self._id = self._pm.extract('id', pType=str)
        self._name = self._pm.extract('name', pType=str)
        self._description = self._pm.extract('description', pType=str)
        self._specificParams = self._params['specific']


class AddAgent(AgentModificationService):

    def _checkParams(self):
        AgentModificationService._checkParams(self)
        self._type = self._pm.extract('type', pType=str)

    def _getAnswer(self):
        sm = SyncManager.getDBInstance()

        avtypes = AgentTypeInspector.getAvailableTypes()

        if self._type not in avtypes:
            raise ServiceError('', 'Agent type %s is unknown' % self._type)

        typeClass = avtypes[self._type]
        access = AdminList().getInstance().getList()[0]

        sm.registerNewAgent(typeClass(self._id, self._name, self._description,
                                      60, access, **self._specificParams))


class AgentOperationBase(AdminService):

    def _checkParams(self):
        self._pm = ParameterManager(self._params)
        AdminService._checkParams(self)
        self._id = self._pm.extract('id', pType=str)
        self._sm = SyncManager.getDBInstance()
        self._agent = self._sm.getAllAgents()[self._id]


class EditAgent(AgentOperationBase, AgentModificationService):

    def _checkParams(self):
        AgentOperationBase._checkParams(self)
        AgentModificationService._checkParams(self)

    def _getAnswer(self):
        self._agent.setParameters(self._description, self._name)

        for param, value in self._specificParams.iteritems():
            self._agent.setExtraOption(param, value)


class DeleteAgent(AgentOperationBase):

    def _getAnswer(self):
        self._sm.removeAgent(self._agent)
        return True


class PreActivateAgent(AgentOperationBase):

    def _getAnswer(self):
        self._agent.preActivate(int_timestamp(nowutc()) / self._sm.getGranularity())
        return True


class ActivateAgent(AgentOperationBase):

    def _getAnswer(self):
        self._agent.setActive(True)
        return True


methodMap = {
    "livesync.addAgent": AddAgent,
    "livesync.editAgent": EditAgent,
    "livesync.deleteAgent": DeleteAgent,
    "livesync.activateAgent": ActivateAgent,
    "livesync.preActivateAgent": PreActivateAgent
}
