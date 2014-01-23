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
Service handlers for search management
"""

from MaKaC.services.implementation.base import AdminService, ParameterManager, TextModificationBase
from indico.ext.search.register import SearchConfig

# JSON Services

class SetDefaultSearchEngineAgent(TextModificationBase, AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        self._pm = ParameterManager(self._params)
        self._agent = self._pm.extract('agent', pType=str)

    def _getAnswer(self):
        SearchConfig().setDefaultSearchEngineAgent(self._agent)
        return True

class GetSearchEngineAgentList(AdminService):

    def _getAnswer(self):
        return SearchConfig().getSearchEngineAgentList()


methodMap = {
    "search.setDefaultSEA": SetDefaultSearchEngineAgent,
    "search.getSEAList": GetSearchEngineAgentList,
}
