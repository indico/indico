# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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
# along with Indico; if not, see <http://www.gnu.org/licenses/>.


from indico.modules.events.layout.views import WPPage
from MaKaC.webinterface.pages.conferences import (WPTPLConferenceDisplay, WPConferenceDisplay, WPConferenceTimeTable,
                                                  WPConferenceProgram, WPContributionList, WPAuthorIndex,
                                                  WPSpeakerIndex)
from MaKaC.webinterface.pages.sessions import WPSessionDisplay
from MaKaC.webinterface.pages.contributions import WPContributionDisplay
from MaKaC.webinterface.pages.registrants import WPConfRegistrantsList, WConfRegistrantsList
from MaKaC.webinterface.pages.subContributions import WPSubContributionDisplay
from MaKaC.webinterface.pages.authors import WPAuthorDisplay


class WPStaticEventBase:
    def _getBaseURL(self):
        return "static"

    def _getHeader(self):
        return ""

    def _getFooter(self):
        return ""

    def getJSFiles(self):
        return (self._asset_env['base_js'].urls() + self._asset_env['modules_event_display_js'].urls() +
                self._asset_env['modules_attachments_js'].urls())


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
        return variables


class WPStaticConferenceDisplay(WPStaticEventBase, WPConferenceDisplay):
    pass


class WPStaticConferenceTimeTable(WPStaticEventBase, WPConferenceTimeTable):
    endpoint = 'event.conferenceTimeTable'

    def getJSFiles(self):
        return WPStaticEventBase.getJSFiles(self) + self._includeJSPackage('Timetable')


class WPStaticConferenceProgram(WPStaticEventBase, WPConferenceProgram):
    endpoint = 'event.conferenceProgram'


class WPStaticContributionList(WPStaticEventBase, WPContributionList):
    endpoint = 'event.contributionListDisplay'

    def _getBody(self, params):
        from MaKaC.webinterface.rh.conferenceDisplay import RHContributionList
        from MaKaC.webinterface.pages.conferences import WConfContributionList
        # Getting an contribution list empty filter
        filterCriteria = RHContributionList.create_filter(self._conf, params)
        wc = WConfContributionList(self._getAW(), self._conf, filterCriteria, "")
        return wc.getHTML()


class WPStaticCustomPage(WPStaticEventBase, WPPage):
    pass


class WPStaticAuthorIndex(WPStaticEventBase, WPAuthorIndex):
    endpoint = 'event.confAuthorIndex'

    def getJSFiles(self):
        return WPStaticEventBase.getJSFiles(self) + WPAuthorIndex.getJSFiles(self) + self._includeJSPackage('authors')


class WPStaticSpeakerIndex(WPStaticEventBase, WPSpeakerIndex):
    endpoint = 'event.confSpeakerIndex'

    def getJSFiles(self):
        return WPStaticEventBase.getJSFiles(self) + WPSpeakerIndex.getJSFiles(self)


class WPStaticSessionDisplay(WPStaticEventBase, WPSessionDisplay):
    def getJSFiles(self):
        return WPStaticEventBase.getJSFiles(self) + self._includeJSPackage('Timetable')


class WPStaticContributionDisplay(WPStaticEventBase, WPContributionDisplay):
    pass


class WPStaticConfRegistrantsList(WPStaticEventBase, WPConfRegistrantsList):
    endpoint = 'event.confRegistrantsDisplay-list'

    def _getBody(self, params):
        from MaKaC.webinterface.rh.registrantsDisplay import RHRegistrantsList
        from MaKaC.webinterface.common import regFilters

        sortingCrit = regFilters.SortingCriteria([params.get("sortBy", "Name").strip()])
        filterCrit = RHRegistrantsList.create_filter(self._conf, params)
        wc = WConfRegistrantsList(self._conf, filterCrit, sortingCrit, None, "session")
        return wc.getHTML()


class WPStaticSubContributionDisplay(WPStaticEventBase, WPSubContributionDisplay):
    pass


class WPStaticAuthorDisplay(WPStaticEventBase, WPAuthorDisplay):
    def getJSFiles(self):
        return WPStaticEventBase.getJSFiles(self) + WPAuthorDisplay.getJSFiles(self)
