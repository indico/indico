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

from xml.sax.saxutils import escape, quoteattr

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.navigation as navigation
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase,WPConferenceBase,WPConferenceDefaultDisplayBase, WConfDisplayFrame
import MaKaC.conference as conference
from MaKaC.webinterface.general import strfFileSize
from MaKaC.webinterface.materialFactories import ConfMFRegistry,SessionMFRegistry,ContribMFRegistry
from indico.core.config import Config
from MaKaC.webinterface.pages.category import WPCategoryBase,WPCategoryDisplayBase,WPCategoryDisplay
import MaKaC.webinterface.pages.category
import MaKaC.webinterface.displayMgr as displayMgr
from MaKaC.i18n import _
from indico.util.i18n import i18nformat

class WPMaterialBase( WPConferenceModifBase, WPCategoryBase ):

    def __init__( self, rh, material ):
        self._material = self._target = material
        if self._material.getConference()!=None:
            WPConferenceModifBase.__init__( self, rh, self._material.getConference() )
        else:
            WPCategoryBase.__init__(self,rh,self._material.getCategory())

    def _getFooter( self ):
        """
        """

        wc = wcomponents.WFooter()

        if self._conf != None:
            p = {"modificationDate":self._conf.getModificationDate().strftime("%d %B %Y %H:%M"),
                 "subArea": self._getSiteArea() }
            return wc.getHTML(p)
        else:
            return wc.getHTML()


class WPMaterialDisplayBase( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, material):
        self._material = self._target =material
        WPConferenceDefaultDisplayBase.__init__( self, rh, self._material.getConference() )
        self._navigationTarget = self._material

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
               self._includeJSPackage('MaterialEditor')

    def _applyDecoration( self, body ):
        return WPConferenceDefaultDisplayBase._applyDecoration( self, body )

    def _getBody( self, params ):

        wc = WMaterialDisplay( self._getAW(), self._material )
        pars = { "fileAccessURLGen": urlHandlers.UHFileAccess.getURL }
        return wc.getHTML( pars )


class WPMaterialCatDisplayBase(WPCategoryDisplayBase, WPMaterialDisplayBase ):
    def __init__(self, rh, material):
        self._material = self._target =material


        WPCategoryDisplayBase.__init__(self,rh,self._material.getCategory())
        self._navigationTarget = self._material

    def _applyDecoration( self, body ):

        return WPCategoryDisplayBase._applyDecoration( self, body )

    def _getBody( self, params ):

        wc = WMaterialDisplay( self._getAW(), self._material )
        return wc.getHTML( )


class WPMaterialConfDisplayBase(WPMaterialDisplayBase, WPConferenceDefaultDisplayBase ):

    def __init__(self,rh,material):
        self._material = self._target =material

        WPConferenceDefaultDisplayBase.__init__(self,rh,self._material.getConference())

        self._navigationTarget = self._material

    def _applyDecoration( self, body ):

        return WPConferenceDefaultDisplayBase._applyDecoration( self, body )


class WMaterialDisplay(wcomponents.WTemplated):

    def __init__(self, aw, material):
        self._material=material
        self._aw=aw

    def _canSubmitResource(self, material):
        if isinstance(material.getOwner(), conference.Contribution):
            contrib=material.getOwner()
            status=contrib.getCurrentStatus()
            if not isinstance(status,conference.ContribStatusWithdrawn) and \
                                contrib.canUserSubmit(self._aw.getUser()):
                return True
        return False

    def _getURL(self, resource):
        url = resource.getURL()
        if url.find(".wmv") != -1:
            url = urlHandlers.UHVideoWmvAccess().getURL(resource)
        elif url.find(".flv") != -1 or url.find(".f4v") != -1 or url.find("rtmp://") != -1:
            url = urlHandlers.UHVideoFlashAccess().getURL(resource)
        return url

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["canSubmitResource"] = self._canSubmitResource(self._material)
        vars["material"] = self._material
        vars["accessWrapper"] = self._aw
        vars["getURL"] = lambda resource : self._getURL(resource)
        vars["fileAccessURLGen"] = urlHandlers.UHFileAccess.getURL
        if self._material.getSubContribution():
            vars["uploadAction"] = 'Indico.Urls.UploadAction.subcontribution'
        elif self._material.getContribution():
            vars["uploadAction"] = 'Indico.Urls.UploadAction.contribution'
        elif self._material.getSession():
            vars["uploadAction"] = 'Indico.Urls.UploadAction.session'
        elif self._material.getConference():
            vars["uploadAction"] = 'Indico.Urls.UploadAction.conference'
        else:
            vars["uploadAction"] = 'Indico.Urls.UploadAction.category'

        return vars

