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

import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.color as color
from MaKaC.i18n import _

class RHSimpleColorChart( base.RH ):
    _uh = urlHandlers.UHSimpleColorChart

    def _checkParams( self, params ):
        base.RH._checkParams( self, params )
        self._colorCodeTarget = params.get( "colorCodeTarget", "")
        self._colorPreviewTarget = params.get( "colorPreviewTarget", "")
        if self._colorCodeTarget.strip()=="":
            raise MaKaCError( _("Color code target error: please, indicate the target of the color code"))
        if self._colorPreviewTarget.strip()=="":
            raise MaKaCError( _("Color preview target error: please, indicate the target of the color preview"))
        self._formId=params.get( "formId", "0")
    
    def _process( self ):
        p = color.WPSimpleColorChart( self, self._colorCodeTarget, self._colorPreviewTarget, self._formId )
        return p.display()
