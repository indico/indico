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

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.pages.conferences import WPConferenceBase, WPConferenceModifBase, WPConferenceDefaultDisplayBase
from indico.core.config import Config
import MaKaC.webinterface.navigation as navigation
from MaKaC.webinterface.general import strfFileSize
from MaKaC.webinterface.pages.base import WPNotDecorated
from MaKaC.webinterface.pages.category import WPCategoryBase
import MaKaC.webinterface.pages.category
from MaKaC.i18n import _


class WPFileBase( WPConferenceModifBase, WPCategoryBase):

    def __init__( self, rh, file ):
        self._file = file

        if self._file.getConference()!=None:

            WPConferenceModifBase.__init__( self, rh, self._file.getConference() )

        else:
            WPCategoryBase.__init__(self,rh,self._file.getCategory())

class WPVideoWmv( WPFileBase ):

    def _getBody( self, params ):
        return WVideoWmv(self._file).getHTML()

class WVideoWmv( wcomponents.WTemplated ):

    def __init__( self, file ):
        self._file = file

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["url"] = self._file.getURL()
        vars["downloadurl"] = self._file.getURL().replace("mms://","http://")
        return vars

class WPVideoFlash( WPFileBase ):

    def _getBody( self, params ):
        return WVideoFlash(self._file).getHTML()

class WVideoFlash( wcomponents.WTemplated ):

    def __init__( self, file ):
        self._file = file

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["indicobaseurl"] = Config.getInstance().getBaseURL()
        url = vars["url"] = self._file.getURL()
        vars["download"] = ""
        if url.find("http://") != -1:
            vars["download"] = """<a href="%s">Download File</a>""" % url
        return vars

class WPMinutesDisplay(WPNotDecorated):
    navigationEntry=navigation.NEMaterialDisplay

    def __init__(self,rh,file):
        WPNotDecorated.__init__(self,rh)
        self._file=file

    def _getBody(self,params):
        wc=wcomponents.WMinutesDisplay(self._file)
        return wc.getHTML(params)
