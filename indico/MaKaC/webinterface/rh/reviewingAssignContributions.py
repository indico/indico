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

import os
from MaKaC.errors import NoReportError
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.pages.reviewing import WPConfReviewingAssignContributions
from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager, RCReferee
from MaKaC.common.contribPacker import ZIPFileHandler, ReviewingPacker
from indico.web.flask.util import send_file


class RHReviewingAssignContributionsList(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifListContribToJudge

    def _checkProtection(self):
        if not RCPaperReviewManager.hasRights(self) and not RCReferee.hasRights(self):
            RHConferenceModifBase._checkProtection(self)

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

    def _process( self ):
        p = WPConfReviewingAssignContributions(self, self._target)
        return p.display()


class RHDownloadAcceptedPapers(RHConferenceModifBase):

    def _checkProtection(self):
        if not RCPaperReviewManager.hasRights(self):
            RHConferenceModifBase._checkProtection(self)

    def _process(self):
        p = ReviewingPacker(self._conf)
        path = p.pack(ZIPFileHandler())
        if not os.path.getsize(path):
            raise NoReportError(_('There are no accepted papers.'))
        return send_file('accepted-papers.zip', path, 'ZIP', inline=False)
