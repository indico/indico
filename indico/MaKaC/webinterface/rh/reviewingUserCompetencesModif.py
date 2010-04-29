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
                self._conf.getConfReview().addUserCompetences(self._user, self._competences)
            if self._remove:
                self._conf.getConfReview().removeUserCompetences(self._user, self._competences)
            self._redirect(urlHandlers.UHConfModifUserCompetences.getURL(self._conf))
        