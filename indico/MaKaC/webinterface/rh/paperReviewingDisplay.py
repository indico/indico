# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
import MaKaC.webinterface.rh.base as base
from MaKaC.webinterface.pages.paperReviewingDisplay import WPPaperReviewingDisplay, \
            WPDownloadPRTemplate, WPUploadPaper


class RHPaperReviewingDisplay(RHConferenceBaseDisplay, base.RHProtected):

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        p = WPPaperReviewingDisplay( self, self._target)
        return p.display()

class RHDownloadPRTemplate(RHConferenceBaseDisplay, base.RHProtected):

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        p = WPDownloadPRTemplate( self, self._target)
        return p.display()


class RHUploadPaper(RHConferenceBaseDisplay ,base.RHProtected):

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        p = WPUploadPaper(self,self._target)
        return p.display()