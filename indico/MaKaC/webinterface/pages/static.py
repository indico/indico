# -*- coding: utf-8 -*-
#
#
# This file is part of Indico.
# Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico;if not, see <http://www.gnu.org/licenses/>.


from MaKaC.webinterface.pages.conferences import WPTPLConferenceDisplay, WPConferenceDisplay, WPConferenceTimeTable, WPConferenceProgram, WPContributionList, WPInternalPageDisplay, WPAuthorIndex, WPSpeakerIndex
from MaKaC.webinterface.pages.sessions import WPSessionDisplay
from MaKaC.webinterface.pages.contributions import WPContributionDisplay
from MaKaC.webinterface.pages.registrants import WPConfRegistrantsList, WConfRegistrantsList
from MaKaC.webinterface.pages.material import WPMaterialConfDisplayBase
from MaKaC.webinterface.pages.subContributions import WPSubContributionDisplay
from MaKaC.webinterface.pages.authors import WPAuthorDisplay
from MaKaC.webinterface.displayMgr import SystemLink
from indico.util.contextManager import ContextManager


class WPStaticEventBase:

    def _getBaseURL(self):
        return "static"

    def _getHeader(self):
        return ""

    def _getFooter(self):
        return ""

    def getJSFiles(self):
        return self._asset_env['base_js'].urls()

    def _getMenu(self):
        for link in self._sectionMenu.getLinkList():
            if isinstance(link, SystemLink) and link.getName() not in ContextManager.get("_menu_offline_items"):
                link.setVisible(False)


class WPTPLStaticConferenceDisplay(WPStaticEventBase, WPTPLConferenceDisplay):

    def _extractInfoForButton(self, item):
        info = {}
        for key in ['sessId', 'slotId', 'contId', 'subContId']:
            info[key] = 'null'
        info['confId'] = self._conf.getId()
        return info

    def _getVariables(self, conf):
        variables = WPTPLConferenceDisplay._getVariables(self, conf)
        variables['registrationOpen'] = False
        variables['evaluationLink'] = False
        return variables


class WPStaticConferenceDisplay(WPStaticEventBase, WPConferenceDisplay):

    def _defineSectionMenu(self):
        WPConferenceDisplay._defineSectionMenu(self)
        self._getMenu()


class WPStaticConferenceTimeTable(WPStaticEventBase, WPConferenceTimeTable):

    def _defineSectionMenu(self):
        WPConferenceTimeTable._defineSectionMenu(self)
        self._getMenu()

    def getJSFiles(self):
        return WPStaticEventBase.getJSFiles(self) + self._includeJSPackage('Timetable')


class WPStaticConferenceProgram(WPStaticEventBase, WPConferenceProgram):

    def _defineSectionMenu(self):
        WPConferenceProgram._defineSectionMenu(self)
        self._getMenu()


class WPStaticContributionList(WPStaticEventBase, WPContributionList):

    def _defineSectionMenu(self):
        WPContributionList._defineSectionMenu(self)
        self._getMenu()

    def _getBody(self, params):
        from MaKaC.webinterface.rh.conferenceDisplay import RHContributionList
        from MaKaC.webinterface.pages.conferences import WConfContributionList
        # Getting an contribution list empty filter
        filterCriteria = RHContributionList.create_filter(self._conf, params)
        wc = WConfContributionList(self._getAW(), self._conf, filterCriteria, "")
        return wc.getHTML()


class WPStaticInternalPageDisplay(WPStaticEventBase, WPInternalPageDisplay):

    def _defineSectionMenu(self):
        WPInternalPageDisplay._defineSectionMenu(self)
        self._getMenu()


class WPStaticAuthorIndex(WPStaticEventBase, WPAuthorIndex):

    def _defineSectionMenu(self):
        WPAuthorIndex._defineSectionMenu(self)
        self._getMenu()

    def getJSFiles(self):
        return WPStaticEventBase.getJSFiles(self) + WPAuthorIndex.getJSFiles(self) + self._includeJSPackage('authors')


class WPStaticSpeakerIndex(WPStaticEventBase, WPSpeakerIndex):

    def _defineSectionMenu(self):
        WPSpeakerIndex._defineSectionMenu(self)
        self._getMenu()

    def getJSFiles(self):
        return WPStaticEventBase.getJSFiles(self) + WPSpeakerIndex.getJSFiles(self)


class WPStaticSessionDisplay(WPStaticEventBase, WPSessionDisplay):

    def _defineSectionMenu(self):
        WPSessionDisplay._defineSectionMenu(self)
        self._getMenu()

    def getJSFiles(self):
        return WPStaticEventBase.getJSFiles(self) + self._includeJSPackage('Timetable')


class WPStaticContributionDisplay(WPStaticEventBase, WPContributionDisplay):

    def _defineSectionMenu(self):
        WPContributionDisplay._defineSectionMenu(self)
        self._getMenu()


class WPStaticConfRegistrantsList(WPStaticEventBase, WPConfRegistrantsList):

    def _defineSectionMenu(self):
        WPConfRegistrantsList._defineSectionMenu(self)
        self._getMenu()

    def _getBody(self, params):
        from MaKaC.webinterface.rh.registrantsDisplay import RHRegistrantsList
        from MaKaC.webinterface.common import regFilters

        sortingCrit = regFilters.SortingCriteria([params.get("sortBy", "Name").strip()])
        filterCrit = RHRegistrantsList.create_filter(self._conf, params)
        wc = WConfRegistrantsList(self._conf, filterCrit, sortingCrit, None, "session")
        return wc.getHTML()


class WPStaticMaterialConfDisplayBase(WPStaticEventBase, WPMaterialConfDisplayBase):

    def _defineSectionMenu(self):
        WPMaterialConfDisplayBase._defineSectionMenu(self)
        self._getMenu()


class WPStaticSubContributionDisplay(WPStaticEventBase, WPSubContributionDisplay):

    def _defineSectionMenu(self):
        WPSubContributionDisplay._defineSectionMenu(self)
        self._getMenu()

class WPStaticAuthorDisplay(WPStaticEventBase, WPAuthorDisplay):

    def _defineSectionMenu(self):
        WPAuthorDisplay._defineSectionMenu(self)
        self._getMenu()

    def getJSFiles(self):
        return WPStaticEventBase.getJSFiles(self) + WPAuthorDisplay.getJSFiles(self)
