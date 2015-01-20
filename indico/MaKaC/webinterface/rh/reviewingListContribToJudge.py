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

import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.pages.reviewing import WPConfListContribToJudge
from MaKaC.webinterface.pages.reviewing import WPConfListContribToJudgeAsReviewer
from MaKaC.webinterface.pages.reviewing import WPConfListContribToJudgeAsEditor
from MaKaC.errors import MaKaCError

class RHContribListToJudge(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifListContribToJudge

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            confPaperReview = self._conf.getConfPaperReview()
            user = self.getAW().getUser()
            if not (confPaperReview.isReferee(user)):
                raise MaKaCError(_("Only the referees can access this page"))
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

    def _process( self ):
        p = WPConfListContribToJudge(self, self._target)
        return p.display()


class RHContribListToJudgeAsReviewer(RHContribListToJudge):
    _uh = urlHandlers.UHConfModifListContribToJudgeAsReviewer

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            confPaperReview = self._conf.getConfPaperReview()
            user = self.getAW().getUser()
            if not (confPaperReview.isReviewer(user)):
                raise MaKaCError(_("Only the content reviewers can access this page"))
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

    def _process( self ):
        p = WPConfListContribToJudgeAsReviewer(self, self._target)
        return p.display()

class RHContribListToJudgeAsEditor(RHContribListToJudge):
    _uh = urlHandlers.UHConfModifListContribToJudgeAsEditor

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            confPaperReview = self._conf.getConfPaperReview()
            user = self.getAW().getUser()
            if not (confPaperReview.isEditor(user)):
                raise MaKaCError(_("Only the layout reviewers can access this page"))
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

    def _process( self ):
        p = WPConfListContribToJudgeAsEditor(self, self._target)
        return p.display()
