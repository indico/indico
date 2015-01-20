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
import MaKaC.webinterface.pages.reviewing as reviewing
from MaKaC.webinterface.pages.conferences import WPConferenceModificationClosed
import MaKaC.user as user
from MaKaC.webinterface.rh.reviewingModif import RHConfModifReviewingPRMAMBase,\
    RHConfModifReviewingPRMBase
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.errors import MaKaCError
from MaKaC.paperReviewing import ConferencePaperReview as CPR

#class to display the page
class RHConfModifReviewingControl( RHConfModifReviewingPRMAMBase ):
    _uh = urlHandlers.UHConfModifReviewingControl

    def _checkParams( self, params ):
        RHConfModifReviewingPRMAMBase._checkParams( self, params )

    def _process( self ):
        if self._conf.isClosed():
            p = WPConferenceModificationClosed( self, self._target )
        else:
            p = reviewing.WPConfModifReviewingControl( self, self._target)
        return p.display()
