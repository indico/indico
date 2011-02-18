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

from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase
import MaKaC.webinterface.wcomponents as wcomponents

class WPPaperReviewingDisplay(WPConferenceDefaultDisplayBase):

    ''' Display page of paper reviewing '''

    def _getBody(self,params):
        wc = WPaperReviewingDisplay(self._conf)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._paperReviewingOpt)


class WPDownloadPRTemplate(WPConferenceDefaultDisplayBase):

    ''' Class for the page with the list of available templates '''

    def _getBody(self,params):
        wc = WDownloadPRTemplate(self._conf)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._downloadTemplateOpt)


class WPUploadPaper(WPConferenceDefaultDisplayBase):

    ''' Class for the page to upload papers '''

    def _getBody(self,params):
        wc = WUploadPaper(self._getAW(),self._conf)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._uploadPaperOpt)


class WPaperReviewingDisplay(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference


class WDownloadPRTemplate(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        import reviewing
        vars["hasPaperReviewing"] = self._conf.getConfPaperReview().hasReviewing()
        vars["ContributionReviewingTemplatesList"] = reviewing.WContributionReviewingTemplatesList(self._conf).getHTML({"CanDelete" : False})
        return vars


class WUploadPaper(wcomponents.WTemplated):

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def _getContribsHTML(self):
        return WConfPaperMyContributions(self._aw, self._conf).getHTML({})

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["items"]=self._getContribsHTML()
        return vars


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

