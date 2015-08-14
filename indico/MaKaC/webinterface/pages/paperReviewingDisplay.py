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

from MaKaC.webinterface.pages.conferences import WConfDisplayBodyBase
from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase
import MaKaC.webinterface.wcomponents as wcomponents

class WPPaperReviewingDisplay(WPConferenceDefaultDisplayBase):

    ''' Display page of paper reviewing '''
    menu_entry_name = 'paper_reviewing'

    def _getBody(self,params):
        wc = WPaperReviewingDisplay(self._conf)
        return wc.getHTML()


class WPDownloadPRTemplate(WPConferenceDefaultDisplayBase):

    ''' Class for the page with the list of available templates '''
    menu_entry_name = 'download_template'

    def _getBody(self,params):
        wc = WDownloadPRTemplate(self._conf)
        return wc.getHTML()


class WPUploadPaper(WPConferenceDefaultDisplayBase):

    ''' Class for the page to upload papers '''
    menu_entry_name = 'paper_upload'

    def _getBody(self,params):
        wc = WUploadPaper(self._getAW(),self._conf)
        return wc.getHTML()


class WPaperReviewingDisplay(WConfDisplayBodyBase):

    _linkname = 'paper_reviewing'

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        return wvars


class WDownloadPRTemplate(WConfDisplayBodyBase):

    _linkname = 'download_template'

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()

        from MaKaC.webinterface.pages import reviewing
        wvars["hasPaperReviewing"] = self._conf.getConfPaperReview().hasReviewing()
        wvars["ContributionReviewingTemplatesList"] = reviewing.WContributionReviewingTemplatesList(self._conf).getHTML({"CanDelete": False})
        return wvars


class WUploadPaper(WConfDisplayBodyBase):

    _linkname = 'paper_upload'

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def _getContribsHTML(self):
        return WConfPaperMyContributions(self._aw, self._conf).getHTML({})

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["items"] = self._getContribsHTML()
        return wvars


class WConfPaperMyContributions(wcomponents.WTemplated):

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def getHTML(self, params):
        return wcomponents.WTemplated.getHTML(self, params)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["User"] = self._aw.getUser()
        vars["Conference"] = self._conf
        vars["ConfReviewingChoice"] = self._conf.getConfPaperReview().getChoice()
        return vars
