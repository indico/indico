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

import MaKaC.webinterface.pages.category as category
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.conference as conference
from indico.core.config import Config
import MaKaC.common.info as info
from MaKaC.i18n import _
from MaKaC.common.timezoneUtils import DisplayTZ

class WPWelcome( category.WPCategoryDisplay ):

    def __init__(self, rh, target, wfReg):
        category.WPCategoryDisplay.__init__( self, rh, conference.CategoryManager().getRoot(), wfReg )

    def _isFrontPage(self):
        return True;
