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
from cStringIO import StringIO

import os.path
import sys

import MaKaC.webinterface.pages.contributions as contributions
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected,\
    RoomBookingDBMixin
from MaKaC.webinterface.rh.conferenceBase import RHContributionBase
from MaKaC.PDFinterface.conference import ContribToPDF
from MaKaC.common.xmlGen import XMLGen
from indico.core.config import Config
from MaKaC.errors import MaKaCError, ModificationError, NoReportError
import MaKaC.common.timezoneUtils as timezoneUtils
import MaKaC.webinterface.materialFactories as materialFactories
from MaKaC.i18n import _
from indico.web.flask.util import send_file
from indico.web.http_api.hooks.event import ContributionHook
from indico.web.http_api.metadata.serializer import Serializer
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename
from MaKaC.PDFinterface.base import LatexRunner


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
        return send_file(filename, StringIO(data), 'XML')


class RHContributionToPDF(RHContributionDisplay):

    def _process( self ):
        filename = "{0} - Contribution.pdf".format(self._target.getTitle())
        contrib_pdf = ContribToPDF(self._target)
        fpath = contrib_pdf.generate()
        return send_file(filename, fpath, 'PDF')


class RHContributionToiCal(RoomBookingDBMixin, RHContributionDisplay):

    def _process(self):

        if not self._target.isScheduled():
            raise NoReportError(_("You cannot export the contribution with id {0} because it is not scheduled").format(self._target.getId()))

        filename = "{0}-Contribution.ics".format(self._target.getTitle())

        hook = ContributionHook({}, 'contribution', {'event': self._conf.getId(), 'idlist': self._contrib.getId(), 'dformat': 'ics'})
        res = hook(self.getAW())
        resultFossil = {'results': res[0]}

        serializer = Serializer.create('ics')
        return send_file(filename, StringIO(serializer(resultFossil)), 'ICAL')


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
        return send_file(filename, StringIO(xmlgen.getXml()), 'XML')


class RHContributionMaterialSubmissionRightsBase(RHContributionDisplay):

    def _checkProtection(self):
        if not self._target.canModify( self.getAW() )  and not self._target.canUserSubmit(self.getAW().getUser()):
            if self._target.getModifKey() != "":
                raise ModificationError()
            if self._getUser() == None:
                self._checkSessionUser()
            else:
                raise ModificationError()
