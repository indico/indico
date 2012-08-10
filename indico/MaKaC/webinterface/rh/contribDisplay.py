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

import os.path
import sys

import MaKaC.webinterface.pages.contributions as contributions
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected,\
    RoomBookingDBMixin
from MaKaC.webinterface.rh.conferenceBase import RHContributionBase
from MaKaC.PDFinterface.conference import ContribToPDF
from MaKaC.common.xmlGen import XMLGen
from MaKaC.common import Config
from MaKaC.errors import MaKaCError, ModificationError, NoReportError
import MaKaC.common.timezoneUtils as timezoneUtils
import MaKaC.webinterface.materialFactories as materialFactories
from MaKaC.i18n import _
from indico.web.http_api.api import ContributionHook
from indico.util.metadata.serializer import Serializer
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename


class RHContributionDisplayBase( RHContributionBase, RHDisplayBaseProtected ):

    def _checkParams( self, params ):
        RHContributionBase._checkParams( self, params )

    def _checkProtection( self ):
        RHDisplayBaseProtected._checkProtection( self )


class RHContributionDisplay( RoomBookingDBMixin, RHContributionDisplayBase ):
    _uh = urlHandlers.UHContributionDisplay

    def _checkParams( self, params ):
        RHContributionDisplayBase._checkParams( self, params )
        self._hideFull = int(params.get("s",0)) # 1 hide details except paper reviewing

    def _process( self ):
        p = contributions.WPContributionDisplay( self, self._contrib, self._hideFull )
        if self._conf.getType()=="simple_event":
            self._redirect(urlHandlers.UHConferenceDisplay.getURL(self._conf))
        else:
            wf=self.getWebFactory()
            if wf is not None:
                    p = wf.getContributionDisplay( self, self._contrib, self._hideFull)
            return p.display()


class RHContributionToXML(RHContributionDisplay):
    _uh = urlHandlers.UHContribToXML

    def _checkParams( self, params ):
        RHContributionDisplay._checkParams( self, params )
        self._xmltype = params.get("xmltype","standard")

    def _process( self ):
        filename = "%s - contribution.xml"%self._target.getTitle()
        from MaKaC.common.output import outputGenerator, XSLTransformer
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(self.getAW(), xmlgen)
        xmlgen.openTag("event")
        outgen.confToXML(self._target.getConference(),0,1,1,showContribution=self._target.getId(), overrideCache=True)
        xmlgen.closeTag("event")
        basexml = xmlgen.getXml()
        path = Config.getInstance().getStylesheetsDir()
        stylepath = "%s.xsl" % (os.path.join(path,self._xmltype))
        if self._xmltype != "standard" and os.path.exists(stylepath):
            try:
                parser = XSLTransformer(stylepath)
                data = parser.process(basexml)
            except:
                data = "Cannot parse stylesheet: %s" % sys.exc_info()[0]
        else:
            data = basexml
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "XML" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%cleanHTMLHeaderFilename(filename)
        return data


class RHContributionToPDF(RHContributionDisplay):

    def _process( self ):
        tz = timezoneUtils.DisplayTZ(self._aw,self._target.getConference()).getDisplayTZ()
        filename = "%s - Contribution.pdf"%self._target.getTitle()
        pdf = ContribToPDF(self._target.getConference(), self._target, tz=tz)
        data = pdf.getPDFBin()
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%cleanHTMLHeaderFilename(filename)
        return data


class RHContributionToiCal(RoomBookingDBMixin, RHContributionDisplay):

    def _process( self ):

        if not self._target.isScheduled():
            raise NoReportError(_("You cannot export the contribution with id %s because it is not scheduled")%self._target.getId())

        filename = "%s-Contribution.ics"%self._target.getTitle()

        hook = ContributionHook({}, 'contribution', {'event': self._conf.getId(), 'idlist':self._contrib.getId(), 'dformat': 'ics'})
        res = hook(self.getAW(), self._req)
        resultFossil = {'results': res[0]}

        serializer = Serializer.create('ics')
        data = serializer(resultFossil)

        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "ICAL" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%cleanHTMLHeaderFilename(filename)
        return data

class RHContributionToMarcXML(RHContributionDisplay):

    def _process( self ):
        filename = "%s - Contribution.xml"%self._target.getTitle().replace("/","")
        from MaKaC.common.xmlGen import XMLGen
        from MaKaC.common.output import outputGenerator
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(self.getAW(), xmlgen)
        xmlgen.openTag("marc:record", [["xmlns:marc","http://www.loc.gov/MARC21/slim"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"]])
        outgen.contribToXMLMarc21(self._target, xmlgen)
        xmlgen.closeTag("marc:record")
        data = xmlgen.getXml()
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "XML" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%cleanHTMLHeaderFilename(filename)
        return data


class RHContributionMaterialSubmissionRightsBase(RHContributionDisplay):

    def _checkProtection(self):
        if not self._target.canModify( self.getAW() )  and not self._target.canUserSubmit(self.getAW().getUser()):
            if self._target.getModifKey() != "":
                raise ModificationError()
            if self._getUser() == None:
                self._checkSessionUser()
            else:
                raise ModificationError()

class RHContributionDisplayRemoveMaterial( RHContributionDisplay ):
    _uh = urlHandlers.UHContributionDisplayRemoveMaterial

    def _checkProtection(self):
        RHContributionDisplay._checkProtection(self)
        if not self._contrib.canUserSubmit(self._aw.getUser()):
            raise MaKaCError( _("you are not authorised to manage material for this contribution"))

    def _checkParams( self, params ):
        RHContributionDisplay._checkParams( self, params )
        self._materialIds = self._normaliseListParam( params.get("deleteMaterial", []) )
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")
        self._remove=params.has_key("confirm")

    def _process( self ):
        if self._materialIds != []:
            if self._confirmed:
                if self._remove:
                    for id in self._materialIds:
                        #Performing the deletion of special material types
                        f = materialFactories.ContribMFRegistry().getById( id )
                        if f:
                            f.remove( self._target )
                        else:
                            #Performs the deletion of additional material types
                            mat = self._target.getMaterialById( id )
                            self._target.removeMaterial( mat )
            else:
                for id in self._materialIds:
                    #Performing the deletion of special material types
                    f = materialFactories.ContribMFRegistry().getById( id )
                    if f:
                        mat=f.get(self._contrib)
                    else:
                        #Performs the deletion of additional material types
                        mat = self._target.getMaterialById( id )
                    break
                wp = contributions.WPContributionDisplayRemoveMaterialsConfirm(self, self._conf, mat)
                return wp.display()
        self._redirect( urlHandlers.UHContributionDisplay.getURL( self._target ) )

