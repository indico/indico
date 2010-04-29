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

import tempfile,os

import MaKaC.webinterface.pages.material as material
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC import conference, user, domain
from MaKaC.webinterface.rh.conferenceBase import RHMaterialBase
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.common import Config
from MaKaC.errors import FormValuesError
from MaKaC.export import fileConverter

class RHMaterialModifBase( RHMaterialBase, RHModificationBaseProtected ):
    
    def _checkParams( self, params ):
        RHMaterialBase._checkParams( self, params )

    def _checkProtection( self ):
        if self._material.getSession() != None:
            if self._material.getSession().canCoordinate(self.getAW(), "modifContribs"):
                return
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

class RHMaterialModification( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialModification
    
    def _process( self ):
        p = material.WPMaterialModification( self, self._material )
        return p.display()


class RHMaterialModifyData( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialModifyData

    def _process( self ):
        p = material.WPMaterialDataModification( self, self._material )
        return p.display()



class RHMaterialPerformModifyData( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialPerformModifyData

    def _process( self ):
        self._material.setValues( self._getRequestParams() )
        self._redirect( urlHandlers.UHMaterialModification.getURL( self._material ) )


class RHMaterialAddLink( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialLinkCreation

    def _process( self ):
       p = material.WPMaterialLinkCreation( self, self._material )
       return p.display()


class RHMaterialPerformAddLink( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialPerformLinkCreation

    def _process( self ):
        params = self._getRequestParams()
        l = conference.Link()
        l.setName( params["title"] )
        l.setDescription( params["description"] )
        l.setURL( params["url"] )
        self._material.addResource( l )
        self._redirect( urlHandlers.UHMaterialModification.getURL( self._material ) )


class RHMaterialAddFile( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialFileCreation

    def _process( self ):
       p = material.WPMaterialFileCreation( self, self._material )
       return p.display()


class RHMaterialPerformAddFile( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialPerformFileCreation
    
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

    def _checkParams( self, params ):
        RHMaterialModifBase._checkParams( self, params )
        if not params.has_key("file") or type(params["file"]) == str:
            raise FormValuesError("You must choose a local file to be uploaded")
        if not hasattr(self, "_filePath"):
            # do not save the file again if it has already been done (db conflicts)
            self._filePath = self._saveFileToTemp( params["file"].file )
            self._tempFilesToDelete.append(self._filePath)
        self._fileName = params["file"].filename
        self._topdf=params.has_key("topdf")

    def _process( self ):
        params = self._getRequestParams()
        f = conference.LocalFile()
        f.setDescription( params["description"] )
        f.setFileName( self._fileName )
        f.setFilePath( self._filePath )
        title=f.getFileName()
        if params.get("title", "").strip() != "":
           title=params.get("title") 
        f.setName( title)
        self._material.addResource( f )

        #apply conversion
        if self._topdf and fileConverter.CDSConvFileConverter.hasAvailableConversionsFor(os.path.splitext(f.getFileName())[1].strip().lower()):
            fileConverter.CDSConvFileConverter.convert(f.getFilePath(), "pdf", self._material)
        
        self._redirect( urlHandlers.UHMaterialModification.getURL( self._material ) )


class RHMaterialRemoveResources( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialRemoveResources
    
    def _checkParams( self, params ):
        RHMaterialModifBase._checkParams( self, params )
        self._res = []
        resIdList = params.get("removeResources", [] )
        for resId in self._normaliseListParam( resIdList ):
            self._res.append( self._material.getResourceById( resId ) )

    def _process( self ):
        for res in self._res:
            self._material.removeResource( res )
        self._redirect( urlHandlers.UHMaterialModification.getURL( self._material ) )


class RHMaterialModifAC( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialModifAC
    
    def _process( self ):
        p = material.WPMaterialModifAC( self, self._material )
        return p.display()


class RHMaterialSetPrivacy( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialSetPrivacy
    
    def _checkParams( self, params ):
        RHMaterialModifBase._checkParams( self, params )
        privacy = params.get("visibility","PUBLIC")
        self._protect = 0
        if privacy == "PRIVATE":
            self._protect = 1
        elif privacy == "PUBLIC":
            self._protect = 0
        elif privacy == "ABSOLUTELY PUBLIC":
            self._protect = -1
    
    def _process( self ):
        self._material.setProtection( self._protect )
        self._redirect( urlHandlers.UHMaterialModifAC.getURL( self._material ) )

class RHMaterialSetVisibility( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialSetVisibility
    
    def _checkParams( self, params ):
        RHMaterialModifBase._checkParams( self, params )
        self._hidden = params.get( "visibility", "VISIBLE") == "HIDDEN"
    
    def _process( self ):
        self._material.setHidden( self._hidden )
        self._redirect( urlHandlers.UHMaterialModifAC.getURL( self._material ) )

class RHMaterialSetAccessKey( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialSetAccessKey
    
    def _checkParams( self, params ):
        RHMaterialModifBase._checkParams( self, params )
        self._accessKey = params.get( "accessKey", "")
    
    def _process( self ):
        self._material.setAccessKey( self._accessKey )
        self._redirect( urlHandlers.UHMaterialModifAC.getURL( self._material ) )


class RHMaterialSelectAllowed( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialSelectAllowed
    
    def _process( self ):
        p = material.WPMaterialSelectAllowed( self, self._material )
        return p.display( **self._getRequestParams() )


class RHMaterialAddAllowed( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialAddAllowed
    
    def _checkParams( self, params ):
        RHMaterialModifBase._checkParams( self, params )
        selAllowedId = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
        #ah = user.AvatarHolder()
        ph = user.PrincipalHolder()
        self._allowed = []
        for id in selAllowedId:
            self._allowed.append( ph.getById( id ) )
    
    def _process( self ):
        for av in self._allowed:
            self._target.grantAccess( av )
        self._redirect( urlHandlers.UHMaterialModifAC.getURL( self._material ) )


class RHMaterialRemoveAllowed( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialRemoveAllowed

    def _checkParams( self, params ):
        RHMaterialModifBase._checkParams( self, params )
        selAllowedId = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
        #ah = user.AvatarHolder()
        ph = user.PrincipalHolder()
        self._allowed = []
        for id in selAllowedId:
            self._allowed.append( ph.getById( id ) )
    
    def _process( self ):
        for av in self._allowed:
            self._target.revokeAccess( av )
        self._redirect( urlHandlers.UHMaterialModifAC.getURL( self._material ) )


class RHMaterialAddDomains( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialAddDomains
    
    def _process( self ):
        params = self._getRequestParams()
        if ("addDomain" in params) and (len(params["addDomain"])!=0):
            dh = domain.DomainHolder()
            for domId in self._normaliseListParam( params["addDomain"] ):
                self._target.requireDomain( dh.getById( domId ) )
        self._redirect( urlHandlers.UHMaterialModifAC.getURL( self._target ) )


class RHMaterialRemoveDomains( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialRemoveDomains
    
    def _process( self ):
        params = self._getRequestParams()
        if ("selectedDomain" in params) and (len(params["selectedDomain"])!=0):
            dh = domain.DomainHolder()
            for domId in self._normaliseListParam( params["selectedDomain"] ):
                self._target.freeDomain( dh.getById( domId ) )
        self._redirect( urlHandlers.UHMaterialModifAC.getURL( self._target ) )

class RHMaterialMainResourceSelect( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialMainResourceSelect
    
    def _process( self ):
        p = material.WPMaterialMainResourceSelect( self, self._material )
        return p.display( **self._getRequestParams() )


class RHMaterialMainResourcePerformSelect( RHMaterialModifBase ):
    _uh = urlHandlers.UHMaterialMainResourcePerformSelect
     
    def _checkParams( self, params ):
        RHMaterialModifBase._checkParams( self, params )
        self._mainResourceID = params.get("mainResource","")
        self._cancel = params.has_key("cancel")
            
    def _process( self ):
        if not self._cancel:
            if self._mainResourceID.strip().lower() == "none":
                self._material.setMainResource(None)
            elif self._mainResourceID.strip() != "":
                r = self._material.getResourceById(str(self._mainResourceID))
                self._material.setMainResource(r)
        self._redirect( urlHandlers.UHMaterialModification.getURL( self._material ) )
        
