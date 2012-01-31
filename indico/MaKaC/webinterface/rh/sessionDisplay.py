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

import MaKaC.webinterface.pages.sessions as sessions
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common.general import *
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected,\
    RoomBookingDBMixin
from MaKaC.webinterface.rh.conferenceBase import RHSessionBase
from MaKaC.webinterface.common.contribFilters import SortingCriteria
from MaKaC.common import Config
from indico.web.http_api.api import SessionHook
from indico.util.metadata.serializer import Serializer


class RHSessionDisplayBase( RHSessionBase, RHDisplayBaseProtected ):

    def _checkParams( self, params ):
        RHSessionBase._checkParams( self, params )

    def _checkProtection( self ):
        RHDisplayBaseProtected._checkProtection( self )


class RHSessionDisplay( RoomBookingDBMixin, RHSessionDisplayBase ):
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
        filename = "%s-Session.ics"%self._session.getTitle()

        hook = SessionHook({}, 'session', {'event': self._conf.getId(), 'idlist':self._session.getId(), 'dformat': 'ics'})
        res = hook(self.getAW(), self._req)
        resultFossil = {'results': res[0]}

        serializer = Serializer.create('ics')
        data = serializer(resultFossil)

        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "ICAL" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename.replace("\r\n"," ")
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
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename.replace("\r\n"," ")
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
