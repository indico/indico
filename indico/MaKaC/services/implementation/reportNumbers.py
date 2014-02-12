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

from MaKaC.services.implementation.base import ParameterManager, ServiceBase
from MaKaC.services.implementation.contribution import ContributionModifBase
from MaKaC.services.implementation.conference import ConferenceModifBase
from indico.core.config import Config


class GetReportNumberSystems(ServiceBase):

    def _getAnswer(self):
        systems = Config.getInstance().getReportNumberSystems()
        return dict([(system, systems[system]["name"]) for system in systems])

class ReportNumberBase:

    def _checkParams(self):
        pm = ParameterManager(self._params)
        self._reportNumber = pm.extract("reportNumber", pType=str, allowEmpty=False)
        self._reportNumberSystem = pm.extract("reportNumberSystem", pType=str, allowEmpty=False)

class ReportNumberAdd(ReportNumberBase):

    def _getAnswer(self):
        self._target.getReportNumberHolder().addReportNumber(self._reportNumberSystem, self._reportNumber)
        if self._reportNumberSystem in Config.getInstance().getReportNumberSystems().keys():
            reportNumberId="s%sr%s"%(self._reportNumberSystem, self._reportNumber)
            name = Config.getInstance().getReportNumberSystems()[self._reportNumberSystem]["name"]
            return {"id":reportNumberId, "name":name , "system":self._reportNumberSystem, "number": self._reportNumber}
        else:
            return {}


class ReportNumberRemove(ReportNumberBase):

    def _getAnswer(self):
        self._target.getReportNumberHolder().removeReportNumber(self._reportNumberSystem, self._reportNumber)
        return True


class ConferenceAddReportNumber(ReportNumberAdd, ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        ReportNumberAdd._checkParams(self)


class ConferenceRemoveReportNumber(ReportNumberRemove, ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        ReportNumberRemove._checkParams(self)


class ContributionAddReportNumber(ReportNumberAdd, ContributionModifBase):

    def _checkParams(self):
        ContributionModifBase._checkParams(self)
        ReportNumberAdd._checkParams(self)


class ContributionRemoveReportNumber(ReportNumberRemove, ContributionModifBase):

    def _checkParams(self):
        ContributionModifBase._checkParams(self)
        ReportNumberRemove._checkParams(self)


class SubContributionAddReportNumber(ReportNumberAdd, ContributionModifBase):

    def _checkParams(self):
        ContributionModifBase._checkParams(self)
        ReportNumberAdd._checkParams(self)
        subContId = self._pm.extract("subcontribId", pType=str, allowEmpty=False)
        self._target = self._contribution.getSubContributionById(subContId)


class SubContributionRemoveReportNumber(ReportNumberRemove, ContributionModifBase):

    def _checkParams(self):
        ContributionModifBase._checkParams(self)
        ReportNumberRemove._checkParams(self)
        subContId = self._pm.extract("subcontribId", pType=str, allowEmpty=False)
        self._target = self._contribution.getSubContributionById(subContId)


methodMap = {
    "get": GetReportNumberSystems,
    "conference.addReportNumber": ConferenceAddReportNumber,
    "conference.removeReportNumber": ConferenceRemoveReportNumber,
    "contribution.addReportNumber": ContributionAddReportNumber,
    "contribution.removeReportNumber": ContributionRemoveReportNumber,
    "subcontribution.addReportNumber": SubContributionAddReportNumber,
    "subcontribution.removeReportNumber": SubContributionRemoveReportNumber,
}
