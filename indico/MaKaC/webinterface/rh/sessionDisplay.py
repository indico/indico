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

import MaKaC.webinterface.pages.sessions as sessions
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common.general import *
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected 
from MaKaC.webinterface.rh.conferenceBase import RHSessionBase, RHSubmitMaterialBase
from MaKaC.webinterface.common.contribFilters import SortingCriteria
from MaKaC.errors import ModificationError
from MaKaC.ICALinterface.conference import SessionToiCal
from MaKaC.common import Config


class RHSessionDisplayBase( RHSessionBase, RHDisplayBaseProtected ):

    def _checkParams( self, params ):
        RHSessionBase._checkParams( self, params )

    def _checkProtection( self ):
        RHDisplayBaseProtected._checkProtection( self )


class RHSessionDisplay( RHSessionDisplayBase ):
    _uh = urlHandlers.UHSessionDisplay
    
    def _checkParams( self, params ):
        RHSessionDisplayBase._checkParams( self, params )
        self._activeTab=params.get("tab","")
        self._sortingCrit=None
        sortBy=params.get("sortBy","")
        if sortBy.strip()!="":
            self._sortingCrit=SortingCriteria([sortBy])

    def _process( self ):
        p = sessions.WPSessionDisplay(self,self._session)
        wf = self.getWebFactory()
        if wf != None:
            p=wf.getSessionDisplay(self,self._session)
        return p.display(activeTab=self._activeTab,
                        sortingCrit=self._sortingCrit)

class RHSessionToiCal(RHSessionDisplay):
    
    def _process( self ):
        filename = "%s - Session.ics"%self._session.getTitle()
        ical = SessionToiCal(self._session.getConference(), self._session)
        data = ical.getBody()
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "ICAL" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data
     
class RHSessionToMarcXML(RHSessionDisplay):
    
    def _process( self ):
        filename = "%s - Session.xml"%self._session.getTitle().replace("/","")
        from MaKaC.common.xmlGen import XMLGen
        from MaKaC.common.output import outputGenerator
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(self.getAW(), xmlgen)
        xmlgen.openTag("marc:record", [["xmlns:marc","http://www.loc.gov/MARC21/slim"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"]])
        outgen.sessionToXMLMarc21(self._session, xmlgen)
        xmlgen.closeTag("marc:record")
        data = xmlgen.getXml()
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "XML" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data
        

class RHSessionDisplayRemoveMaterial( RHSessionDisplay ):
    _uh = urlHandlers.UHSessionDisplayRemoveMaterial

    def _checkProtection(self):
        RHSessionDisplay._checkProtection(self)
        if not self._target.canModify( self.getAW() ):
            raise MaKaCError("you are not authorised to manage material for this session")
    
    def _checkParams( self, params ):
        RHSessionDisplay._checkParams( self, params )
        self._materialIds = self._normaliseListParam( params.get("deleteMaterial", []) )
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")
        self._remove=params.has_key("confirm")
        
    def _process( self ):
        if self._materialIds != []:
            if self._confirmed:
                if self._remove:
                    for id in self._materialIds:
                        #Performing the deletion of special material types
                        f = materialFactories.SessionMFRegistry.getById( id )
                        if f:
                            f.remove( self._target )
                        else:
                            #Performs the deletion of additional material types
                            mat = self._target.getMaterialById( id )
                            self._target.removeMaterial( mat )
            else:
                for id in self._materialIds:
                    #Performing the deletion of special material types
                    f = materialFactories.SessionMFRegistry.getById( id )
                    if f:
                        mat=f.get(self._contrib)
                    else:
                        #Performs the deletion of additional material types
                        mat = self._target.getMaterialById( id )
                    break
                wp = sessions.WPSessionDisplayRemoveMaterialsConfirm(self, self._conf, mat)
                return wp.display()
        self._redirect( urlHandlers.UHSessionDisplay.getURL( self._target ) )


class RHWriteMinutes( RHSessionDisplayBase ):

    def _checkProtection(self):
        if not self._target.canModify( self.getAW() ) and not self._target.canCoordinate(self.getAW()):
            if self._target.getModifKey() != "":
                raise ModificationError()
            if self._getUser() == None:
                # there is a risk the session was closed during the write
                # process and the minutes will be lost if we do not preserve
                # them
                self._preserveParams()
                # then ask the user to login again
                self._checkSessionUser()
            else:
                raise ModificationError()
    
    def _preserveParams(self):
        preservedParams = self._getRequestParams().copy()
        self._websession.setVar("minutesPreservedParams",preservedParams)

    def _getPreservedParams(self):
        params = self._websession.getVar("minutesPreservedParams")
        if params is None :
            return {}
        return params

    def _removePreservedParams(self):
        self._websession.setVar("minutesPreservedParams",None)

    def _checkParams( self, params ):
        RHSessionDisplayBase._checkParams( self, params )
        preservedParams = self._getPreservedParams()
        if preservedParams != {}:
            params.update(preservedParams)
            self._removePreservedParams()
        self._cancel = params.has_key("cancel")
        self._save = params.has_key("OK")
        self._text = params.get("text", "")#.strip()
        
    def _process( self ):
        wf=self.getWebFactory()
        if self._save:
            minutes = self._target.getMinutes()
            if not minutes:
                minutes = self._target.createMinutes()
            minutes.setText( self._text )
        elif not self._cancel:
            if wf is None:
                wp = sessions.WPSessionDisplayWriteMinutes(self, self._target)
            else:
                wp = wf.getSessionDisplayWriteMinutes( self, self._target)
            return wp.display()
        if wf is None:
            self._redirect( urlHandlers.UHSessionDisplay.getURL( self._target ) )
        else:
            self._redirect( urlHandlers.UHConferenceDisplay.getURL( self._target.getConference() ) )
