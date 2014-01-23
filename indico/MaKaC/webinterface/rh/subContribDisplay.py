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

import MaKaC.webinterface.pages.subContributions as subContributions
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected,\
    RoomBookingDBMixin
from MaKaC.webinterface.rh.conferenceBase import RHSubContributionBase
from indico.core.config import Config
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename
from indico.web.flask.util import send_file


class RHSubContributionDisplayBase( RHSubContributionBase, RHDisplayBaseProtected ):

    def _checkParams( self, params ):
        RHSubContributionBase._checkParams( self, params )

    def _checkProtection( self ):
        RHDisplayBaseProtected._checkProtection( self )


class RHSubContributionDisplay( RoomBookingDBMixin, RHSubContributionDisplayBase ):
    _uh = urlHandlers.UHSubContributionDisplay

    def _process( self ):
        p = subContributions.WPSubContributionDisplay( self, self._subContrib )
        wf=self.getWebFactory()
        if wf is not None:
                p = wf.getSubContributionDisplay( self, self._subContrib)
        return p.display()

class RHSubContributionToMarcXML(RHSubContributionDisplayBase):

    def _process(self):
        filename = "%s - Subcontribution.xml" % self._subContrib.getTitle().replace("/","")
        from MaKaC.common.xmlGen import XMLGen
        from MaKaC.common.output import outputGenerator
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(self.getAW(), xmlgen)
        xmlgen.openTag("marc:record", [["xmlns:marc","http://www.loc.gov/MARC21/slim"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"]])
        outgen.subContribToXMLMarc21(self._subContrib, xmlgen)
        xmlgen.closeTag("marc:record")
        return send_file(filename, StringIO(xmlgen.getXml()), 'XML')
