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

import MaKaC.webinterface.pages.category as category
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.personalization as personalization
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.conference as conference
from MaKaC.common.Configuration import Config
import MaKaC.common.info as info
from MaKaC.common.cache import CategoryCache
from MaKaC.i18n import _
from MaKaC.common.timezoneUtils import DisplayTZ

class WPWelcome( category.WPCategoryDisplay ):
    
    def __init__(self, rh, target, wfReg):
        category.WPCategoryDisplay.__init__( self, rh, conference.CategoryManager().getRoot(), wfReg )

    def _isFrontPage(self):
        return True;
