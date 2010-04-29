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
