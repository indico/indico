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

from MaKaC.webinterface.pages.base import WPNotDecorated
from MaKaC.webinterface.wcomponents import WTemplated
from indico.core.config import Config

class WPSimpleColorChart( WPNotDecorated ):

    def __init__(self, rh, colorCodeTarget, colorPreviewTarget, formId=0):
        WPNotDecorated.__init__(self, rh)
        self._colorCodeTarget = colorCodeTarget
        self._colorPreviewTarget = colorPreviewTarget
        if formId.strip()=="":
            formId="0"
        self._formId=formId

    def _getBody( self, params ):
        wc = WSimpleColorChart()
        #color=""
        #colorpreview=""
        #if self._colorTarget=="background":
        #    color="backgroundColor"
        #    colorpreview="backgroundColorpreview"
        #elif self._colorTarget=="text":
        #    color="textColor"
        #    colorpreview="textColorpreview"
        pars = {"imgColortable": Config.getInstance().getSystemIconURL("colortable"), \
                "colorString":self._colorCodeTarget, \
                "colorPreviewString":self._colorPreviewTarget, \
                "formId":self._formId}

        return wc.getHTML( pars )


class WSimpleColorChart( WTemplated ):

    def getVars( self ):
        vars = WTemplated.getVars( self )
        return vars
