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

import MaKaC.webinterface.rh.admins as admins
import MaKaC.webinterface.urlHandlers as urlHandlers
from indico.core.config import Config
from MaKaC.webinterface.pages import admins as adminPages
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase
from MaKaC.webinterface.pages import conferences
import MaKaC.conference as conference

class RHTemplatesBase(admins.RHAdminBase):
    pass


class RHBadgeTemplates( RHTemplatesBase ):
    _uh = urlHandlers.UHBadgeTemplates

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        p = adminPages.WPBadgeTemplates(self)
        return p.display()

class RHPosterTemplates( RHTemplatesBase ):
    _uh = urlHandlers.UHPosterTemplates

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        p = adminPages.WPPosterTemplates(self)
        return p.display()

class RHSetDefaultPDFOptions( RHTemplatesBase ):
    _uh = urlHandlers.UHTemplatesSetDefaultPDFOptions

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self.__defaultConferencePDFOptions = conference.CategoryManager().getDefaultConference().getBadgeTemplateManager().getPDFOptions()

        try:
            self.__marginTop = float(params.get("marginTop",''))
        except ValueError:
            self.__marginTop = self.__defaultConferencePDFOptions.getTopMargin()

        try:
            self.__marginBottom = float(params.get("marginBottom",''))
        except ValueError:
            self.__marginBottom = self.__defaultConferencePDFOptions.getBottomMargin()

        try:
            self.__marginLeft = float(params.get("marginLeft",''))
        except ValueError:
            self.__marginLeft = self.__defaultConferencePDFOptions.getLeftMargin()

        try:
            self.__marginRight = float(params.get("marginRight",''))
        except ValueError:
            self.__marginRight = self.__defaultConferencePDFOptions.getRightMargin()

        try:
            self.__marginColumns = float(params.get("marginColumns",''))
        except ValueError:
            self.__marginColumns = self.__defaultConferencePDFOptions.getMarginColumns()

        try:
            self.__marginRows = float(params.get("marginRows",''))
        except ValueError:
            self.__marginRows = self.__defaultConferencePDFOptions.getMarginRows()

        self.__pagesize = params.get("pagesize",'A4')

        self.__drawDashedRectangles = params.get("drawDashedRectangles", False) is not False
        self.__landscape = params.get('landscape') == '1'

    def _process( self ):
        self.__defaultConferencePDFOptions.setTopMargin(self.__marginTop)
        self.__defaultConferencePDFOptions.setBottomMargin(self.__marginBottom)
        self.__defaultConferencePDFOptions.setLeftMargin(self.__marginLeft)
        self.__defaultConferencePDFOptions.setRightMargin(self.__marginRight)
        self.__defaultConferencePDFOptions.setMarginColumns(self.__marginColumns)
        self.__defaultConferencePDFOptions.setMarginRows(self.__marginRows)
        self.__defaultConferencePDFOptions.setPagesize(self.__pagesize)
        self.__defaultConferencePDFOptions.setDrawDashedRectangles(self.__drawDashedRectangles)
        self.__defaultConferencePDFOptions.setLandscape(self.__landscape)

        self._redirect(urlHandlers.UHBadgeTemplates.getURL())

class RHTemplateModifBase( RHConferenceBase, RHModificationBaseProtected ):

    def _checkParams( self, params ):
        RHConferenceBase._checkParams( self, params )

    def _checkProtection( self ):
        RHModificationBaseProtected._checkProtection( self )

    def _displayCustomPage( self, wf ):
        return None

    def _displayDefaultPage( self ):
        return None

    def _process( self ):
        wf = self.getWebFactory()
        if wf != None:
            res = self._displayCustomPage( wf )
            if res != None:
                return res
        return self._displayDefaultPage()

class RHConfPosterDesign(RHTemplateModifBase):
    """ This class corresponds to the screen where templates are
        designed. We can arrive to this screen from different scenarios:
         -We are creating a new template (templateId = new template id, new = True)
         -We are editing an existing template (templateId = existing template id, new = False or not set)
    """

    def _checkParams(self, params):
        RHTemplateModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        new = params.get("new",'False')
        if new == 'False':
            self.__new = False
        else:
            self.__new = True

    def _process(self):

        p = adminPages.WPPosterTemplateDesign(self, self._target, self.__templateId, self.__new)
        return p.display()

class RHConfBadgeDesign(RHTemplateModifBase):
    """ This class corresponds to the screen where templates are
        designed. We can arrive to this screen from different scenarios:
         -We are creating a new template (templateId = new template id, new = True)
         -We are editing an existing template (templateId = existing template id, new = False or not set)
    """

    def _checkParams(self, params):
        RHTemplateModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        new = params.get("new",'False')
        if new == 'False':
            self.__new = False
        else:
            self.__new = True

    def _process(self):

        p = adminPages.WPBadgeTemplateDesign(self, self._target, self.__templateId, self.__new)
        return p.display()
