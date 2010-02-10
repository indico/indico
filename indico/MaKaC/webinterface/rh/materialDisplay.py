# -*- coding: utf-8 -*-
##
## $Id: materialDisplay.py,v 1.14 2009/05/14 18:06:03 jose Exp $
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

class RHMaterialDisplay( RHMaterialDisplayBase ):
    _uh = urlHandlers.UHMaterialDisplay
    
    def _process( self ):

        # material pages should not be cached, since protection can change
        self._disableCaching()

        if len(self._material.getResourceList()) == 1:
            res = self._material.getResourceList()[0]
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
            #raise "%s"%self._material.getOwner()
            if self._material.getConference()!=None:
                p = material.WPMaterialConfDisplayBase(self, self._material  )
            else:
                p= material.WPMaterialCatDisplayBase(self, self._material)
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

class RHMaterialDisplayRemoveResource( RHMaterialDisplayModifBase ):
    _uh = urlHandlers.UHMaterialDisplayRemoveResource

    def _checkParams( self, params ):
        RHMaterialDisplayModifBase._checkParams( self, params )
        self._res = None
        if params.get("resId", "") != "":
            self._res = self._material.getResourceById( params.get("resId") )
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")
        self._remove=params.has_key("confirm")

    def _process( self ):
        if self._res is not None:
            if self._confirmed:
                if self._remove:
                    self._material.removeResource( self._res )
            else:
                wf = self.getWebFactory()
                if wf != None:
                    wp = wf.getMaterialDisplayRemoveResourceConfirm(self, self._conf, self._res)
                else:    
                    wp = material.WPMaterialDisplayRemoveResourceConfirm(self, self._conf, self._res)
                return wp.display()
        if self._material.getNbResources()<=1 and isinstance(self._material.getOwner(), conference.Contribution):
            self._redirect( urlHandlers.UHContributionDisplay.getURL( self._material ) )
        else:
            self._redirect( urlHandlers.UHMaterialDisplay.getURL( self._material ) ) 

class RHMaterialDisplaySubmitResource(RHMaterialDisplayModifBase):

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="IndicoFileUpload.tmp", dir = tempPath )[1]
        return tempFileName

    def _saveFileToTemp( self, fd ):
        fileName = self._getNewTempFile()
        f = open( fileName, "wb" )
        f.write( fd.read() )
        f.close()
        return fileName

    def _checkParams(self,params):
        RHMaterialDisplayModifBase._checkParams(self,params)
        self._action=""
        self._overwrite=False
        if params.has_key("CANCEL"):
            self._action="CANCEL"
        elif params.has_key("OK"):
            self._action="SUBMIT_FILES"
            if params.get("file","")=="":
                self._filePath=""
                self._fileName=""
            else:
                if not hasattr(self,"_filePath"):
                    # do not save the file again if it has already been done (db conflicts)
                    self._filePath=self._saveFileToTemp(params["file"].file)
                    self._tempFilesToDelete.append(self._filePath)
                self._fileName=params["file"].filename
            self._matType=params.get("materialType",self._material.getId())
            self._fileDesc=params.get("description","")

    def _getErrorList(self):
        res=[]
        if self._filePath.strip()=="":
            res.append("""- A valid file to be submitted must be specified.""")
        return res

    def _process(self):
        url=urlHandlers.UHMaterialDisplay.getURL(self._target)
        errorList=[]
        if self._action=="CANCEL":
            self._redirect(url)
            return 
        elif self._action=="SUBMIT_FILES":
            errorList=self._getErrorList()
            if len(errorList)==0:
                f=conference.LocalFile()
                f.setName(self._matType)
                f.setDescription(self._fileDesc)
                f.setFileName(self._fileName)
                f.setFilePath(self._filePath)
                self._material.addResource(f)
                self._redirect(url)
                return 
        p=material.WPMaterialDisplaySubmitResource(self,self._target)
        pars=self._getRequestParams()
        pars["errorList"]=errorList
        return  p.display(**self._getRequestParams())


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
