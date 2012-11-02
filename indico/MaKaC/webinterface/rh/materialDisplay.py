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

import tempfile
from MaKaC.errors import MaKaCError
import MaKaC.webinterface.pages.material as material
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.conference as conference
from MaKaC.common.general import *
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected
from MaKaC.webinterface.rh.conferenceBase import RHMaterialBase
from MaKaC.common import Config
from MaKaC.export import fileConverter
from MaKaC.i18n import _

class RHMaterialDisplayBase( RHMaterialBase, RHDisplayBaseProtected ):

    def _checkParams( self, params ):
        RHMaterialBase._checkParams( self, params )

    def _checkProtection( self ):
        RHDisplayBaseProtected._checkProtection( self )


class RHMaterialDisplayModifBase( RHMaterialDisplayBase ):

    def _checkProtection( self ):
        RHMaterialDisplayBase._checkProtection( self )
        #TODO: this checking seems useless!!!! TOCHECK!
        if isinstance(self._material.getOwner(), conference.Contribution):
            self._material.getOwner().canUserSubmit(self._aw.getUser())
        else:
            raise MaKaCError( _("you are not authorised to manage material for this contribution"))


class RHMaterialDisplayCommon:

    def _process(self):
        # material pages should not be cached, since protection can change
        self._disableCaching()

        if len(self._material.getResourceList()) == 1:
            res = self._material.getResourceList()[0]

            self._notify('materialDownloaded', res)

            if isinstance(res, conference.Link):
                url = res.getURL()
                if url.find(".wmv") != -1:
                    urlwmv = urlHandlers.UHVideoWmvAccess().getURL(res)
                    self._redirect( urlwmv )
                elif url.find(".flv") != -1 or url.find(".f4v") != -1 or url.find("rtmp://") != -1:
                    urlflash = urlHandlers.UHVideoFlashAccess().getURL(res)
                    self._redirect( urlflash, noCache=True)
                else:
                    self._redirect( res.getURL(), noCache=True )
            elif isinstance(res, conference.LocalFile):
                self._redirect( urlHandlers.UHFileAccess.getURL( res ), noCache=True )
        else:
            return self._processManyMaterials()


class RHMaterialDisplay( RHMaterialDisplayBase, RHMaterialDisplayCommon ):
    _uh = urlHandlers.UHMaterialDisplay

    def _process(self):
        return RHMaterialDisplayCommon._process(self)

    def _processManyMaterials( self ):
        if self._material.getConference()!=None:
            p = material.WPMaterialConfDisplayBase(self, self._material)
        else:
            p = material.WPMaterialCatDisplayBase(self, self._material)
        wf=self.getWebFactory()

        if wf is not None:
            p = wf.getMaterialDisplay( self, self._material)

        return p.display()


class RHMaterialDisplayStoreAccessKey( RHMaterialDisplayBase ):
    _uh = urlHandlers.UHMaterialEnterAccessKey

    def _checkParams( self, params ):
        RHMaterialDisplayBase._checkParams(self, params )
        self._accesskey = params.get( "accessKey", "" ).strip()

    def _checkProtection( self ):
        pass

    def _process( self ):
        access_keys = self._getSession().getVar("accessKeys")
        if access_keys == None:
            access_keys = {}
        access_keys[self._target.getUniqueId()] = self._accesskey
        self._getSession().setVar("accessKeys",access_keys)
        url = urlHandlers.UHMaterialDisplay.getURL( self._target )
        self._redirect( url )

class RHMaterialAddConvertedFile(RHMaterialDisplayBase):

    def _checkProtection(self):
        pass

    def _checkParams(self,params):
        pass

    def _process( self ):
        params = self._getRequestParams()
        tempFilePath = fileConverter.CDSConvFileConverter.storeConvertedFile(self.getHostIP(), params)
        self._tempFilesToDelete.append(tempFilePath)
        #Normally, you do not have to response anything special.....but we can think about it.
        return params.get("filename","")
