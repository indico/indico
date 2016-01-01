# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from MaKaC.webinterface.rh import base
from MaKaC.common import xmlGen
from MaKaC.conference import CategoryManager


class RHXMLHandlerBase ( base.RH ):

    def _genStatus (self, statusValue, message, XG):
        XG.openTag("status")
        XG.writeTag("value", statusValue)
        XG.writeTag("message", message)
        XG.closeTag("status")

    def _createResponse (self, statusValue, message):
        XG = xmlGen.XMLGen()
        XG.openTag("response")
        self._genStatus(statusValue, message, XG)
        XG.closeTag("response")

        self._responseUtil.content_type = 'text/xml'
        return XG.getXml()


class RHCategInfo( RHXMLHandlerBase ):

    def _checkParams( self, params ):
        self._id = params.get( "id", "" ).strip()
        self._fp = params.get( "fp", "no" ).strip()

    def _getHeader( self, XG ):
        XG.openTag("response")
        XG.openTag("status")
        XG.writeTag("value", "OK")
        XG.writeTag("message", "Returning category info")
        XG.closeTag("status")

    def _getFooter( self, XG ):
        XG.closeTag("response")

    def _getCategXML( self, cat, XG, fp="no" ):
        XG.openTag("categInfo")
        XG.writeTag("title",cat.getTitle())
        XG.writeTag("id",cat.getId())
        if fp == "yes":
            XG.openTag("father")
            if cat.getOwner():
                self._getCategXML(cat.getOwner(),XG,fp)
                fatherid = cat.getOwner().getId()
            XG.closeTag("father")
        XG.closeTag("categInfo")
        return XG.getXml()

    def _process( self ):
        self._responseUtil.content_type = 'text/xml'
        cm = CategoryManager()
        try:
            XG = xmlGen.XMLGen()
            cat = cm.getById(self._id)
            self._getHeader(XG)
            self._getCategXML(cat, XG, self._fp)
            self._getFooter(XG)
            return XG.getXml()
        except:
            value = "ERROR"
            message = "Category does not exist"
        if value != "OK":
            return self._createResponse(value, message)
