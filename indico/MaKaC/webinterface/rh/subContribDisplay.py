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

import tempfile
import os.path

import MaKaC.conference as conference
import MaKaC.webinterface.pages.subContributions as subContributions
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected 
from MaKaC.webinterface.rh.conferenceBase import RHSubContributionBase, RHSubmitMaterialBase
from MaKaC.PDFinterface.conference import ContribToPDF
from MaKaC.ICALinterface.conference import ContribToiCal
from MaKaC.common.xmlGen import XMLGen
from MaKaC.common import Config
from MaKaC.errors import MaKaCError, ModificationError
import MaKaC.webinterface.materialFactories as materialFactories



class RHSubContributionDisplayBase( RHSubContributionBase, RHDisplayBaseProtected ):

    def _checkParams( self, params ):
        RHSubContributionBase._checkParams( self, params )

    def _checkProtection( self ):
        RHDisplayBaseProtected._checkProtection( self )


class RHSubContributionDisplay( RHSubContributionDisplayBase ):
    _uh = urlHandlers.UHSubContributionDisplay
    
    def _process( self ):
        p = subContributions.WPSubContributionDisplay( self, self._subContrib )
        wf=self.getWebFactory()
        if wf is not None:
                p = wf.getSubContributionDisplay( self, self._subContrib)
        return p.display()

class RHSubContributionToMarcXML(RHSubContributionDisplayBase):
    
    def _process( self ):
        filename = "%s - Subcontribution.xml"%self._subContrib.getTitle().replace("/","")
        from MaKaC.common.xmlGen import XMLGen
        from MaKaC.common.output import outputGenerator
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(self.getAW(), xmlgen)
        xmlgen.openTag("marc:record", [["xmlns:marc","http://www.loc.gov/MARC21/slim"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"]])
        outgen.subContribToXMLMarc21(self._subContrib, xmlgen)
        xmlgen.closeTag("marc:record")
        data = xmlgen.getXml()
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "XML" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data
        
class RHWriteMinutes( RHSubContributionDisplayBase ):

    def _checkProtection(self):
        if not self._target.canModify( self.getAW() ):
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
        RHSubContributionDisplayBase._checkParams( self, params )
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
                wp = conferences.WPSubContributionDisplayWriteMinutes(self, self._target)
            else:
                wp = wf.getSubContributionDisplayWriteMinutes( self, self._target)
            return wp.display()
        if wf is None:
            self._redirect( urlHandlers.UHSubContributionDisplay.getURL( self._target ) )
        else:
            self._redirect( urlHandlers.UHConferenceDisplay.getURL( self._target.getConference() ) )

class RHSubmitMaterial(RHSubContributionDisplayBase):

    def _checkProtection(self):
        if not self._target.canModify( self.getAW() ) and not self._target.canUserSubmit( self.getAW().getUser() ):
            if self._target.getModifKey() != "":
                raise ModificationError()
            if self._getUser() == None:
                self._checkSessionUser()
            else:
                raise ModificationError()
    
    #def _checkProtection(self):
    #    if self.getAW().getUser() is None:
    #        self._checkSessionUser()
    #    elif not self._target.canModify(self.getAW()):
    #        raise MaKaCError("you are not authorised to submit material for this subcontribution")

    def _checkParams(self,params):
        RHSubContributionDisplayBase._checkParams(self,params)
        if not hasattr(self, "_rhSubmitMaterial"):
            self._rhSubmitMaterial=RHSubmitMaterialBase(self._target, self)
        self._rhSubmitMaterial._checkParams(params) 

    def _process(self):
        wf=self.getWebFactory()
        if wf is None:
            url=urlHandlers.UHSubContributionDisplay.getURL(self._target)
            p=subContributions.WPSubmitMaterial
        else:
            url=urlHandlers.UHConferenceDisplay.getURL(self._target.getConference())
            p=wf.getSubContribSubmitMaterial
        r=self._rhSubmitMaterial._process(self, self._getRequestParams(), p)
        if r is None:
            self._redirect(url)
        else:
            return r
