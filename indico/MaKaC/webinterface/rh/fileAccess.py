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

import time

import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.conferenceBase import RHFileBase, RHLinkBase
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected
from MaKaC.webinterface.pages import files
from MaKaC.common import Config
from MaKaC.errors import MaKaCError, NoReportError

from email.Utils import formatdate

class RHFileAccess( RHFileBase, RHDisplayBaseProtected ):
    _uh  = urlHandlers.UHFileAccess
    
    def _checkParams( self, params ):
        try:
            RHFileBase._checkParams( self, params )
        except:
            raise NoReportError("The file you try to access does not exist.")

    def _checkProtection( self ):
        RHDisplayBaseProtected._checkProtection( self )
    
    def _process( self ):

        self._disableCaching()

        if self._file.getId() != "minutes":
            #self._req.headers_out["Accept-Ranges"] = "bytes"
            self._req.headers_out["Content-Length"] = "%s"%self._file.getSize()
            self._req.headers_out["Last-Modified"] = "%s"%formatdate(time.mktime(self._file.getCreationDate().timetuple()))
            cfg = Config.getInstance()
            mimetype = cfg.getFileTypeMimeType( self._file.getFileType() )
            self._req.content_type = """%s"""%(mimetype)
            self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%self._file.getFileName()
            return self._file.readBin()
        else:
            p = files.WPMinutesDisplay(self, self._file )
            return p.display()

class RHFileAccessStoreAccessKey( RHFileBase ):
    _uh = urlHandlers.UHFileEnterAccessKey
    
    def _checkParams( self, params ):
        RHFileBase._checkParams(self, params )
        self._accesskey = params.get( "accessKey", "" ).strip()
    
    def _checkProtection( self ):
        pass
        
    def _process( self ):
        access_keys = self._getSession().getVar("accessKeys")
        if access_keys == None:
            access_keys = {}
        access_keys[self._target.getOwner().getUniqueId()] = self._accesskey
        self._getSession().setVar("accessKeys",access_keys)
        url = urlHandlers.UHFileAccess.getURL( self._target )
        self._redirect( url )

        
class RHVideoWmvAccess( RHLinkBase, RHDisplayBaseProtected ):
    _uh  = urlHandlers.UHVideoWmvAccess
    
    def _checkParams( self, params ):
        try:
            RHLinkBase._checkParams( self, params )
        except:
            raise NoReportError("The file you try to access does not exist.")

    def _checkProtection( self ):
        """targets for this RH are exclusively URLs so no protection apply"""
        return
    
    def _process( self ):
        p = files.WPVideoWmv(self, self._link )
        return p.display()
    
class RHVideoFlashAccess( RHLinkBase, RHDisplayBaseProtected ):
    _uh  = urlHandlers.UHVideoFlashAccess
    
    def _checkParams( self, params ):
        try:
            RHLinkBase._checkParams( self, params )
        except:
            raise NoReportError("The file you try to access does not exist.")

    def _checkProtection( self ):
        """targets for this RH are exclusively URLs so no protection apply"""
        return
    
    def _process( self ):
        p = files.WPVideoFlash(self, self._link )
        return p.display()
