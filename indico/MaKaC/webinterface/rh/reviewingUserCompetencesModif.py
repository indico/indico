# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
import MaKaC.webinterface.pages.reviewing as reviewing
from MaKaC.webinterface.pages.conferences import WPConferenceModificationClosed
import MaKaC.user as user
from MaKaC.webinterface.rh.reviewingModif import RHConfModifReviewingPRMAMBase

class RHConfModifUserCompetences( RHConfModifReviewingPRMAMBase ):
    _uh = urlHandlers.UHConfModifUserCompetences

    def _process( self ):
        if self._conf.isClosed():
            p = WPConferenceModificationClosed( self, self._target )
        else:
            p = reviewing.WPConfModifUserCompetences( self, self._target)
        return p.display()
    

class RHConfModifUserCompetencesAbstracts( RHConfModifReviewingPRMAMBase ):
    _uh = urlHandlers.UHConfModifUserCompetences

    def _process( self ):
        if self._conf.isClosed():
            p = WPConferenceModificationClosed( self, self._target )
        else:
            p = reviewing.WPConfModifUserCompetencesAbstracts( self, self._target)
        return p.display()

class RHConfModifModifyUserCompetences( RHConfModifReviewingPRMAMBase ):
    
    def _checkParams( self, params ):
        RHConfModifReviewingPRMAMBase._checkParams( self, params )
        self._add = params.has_key("add")
        self._remove = params.has_key("remove")
        ph = user.PrincipalHolder()
        self._user =  ph.getById( params.get("user"))
        self._competences = [competence.strip() for competence in params.get("competences", '').split(',')]

    def _process( self ):
        if self._conf.isClosed():
            p = WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            if self._add:
                self._conf.getConfPaperReview().addUserCompetences(self._user, self._competences)
            if self._remove:
                self._conf.getConfPaperReview().removeUserCompetences(self._user, self._competences)
            self._redirect(urlHandlers.UHConfModifUserCompetences.getURL(self._conf))
        