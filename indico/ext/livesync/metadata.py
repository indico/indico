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

from MaKaC import conference
from indico.core.config import Config
from MaKaC.common.output import outputGenerator
from MaKaC import accessControl


class MARCXMLGenerator:
    """
    Generates MARCXML based on Indico DB objects
    """

    def  __init__(self, XG):
        # self.categoryRoot = conference.CategoryManager().getRoot()
        self._user = accessControl.AccessWrapper()
        self._XMLGen = XG
        self._config = Config.getInstance()
        self._outGen = outputGenerator(self._user, self._XMLGen)

    def setPermissionsOf(self, avatar):
        """
        Sets access level according to avatar
        """
        self._user.setUser(avatar)

    def generate(self, obj, out=None, overrideCache=False, deleted=False):
        if not out:
            out = self._XMLGen

        if deleted:
            if type(obj) != str:
                raise AttributeError("Expected int id, got '%s'" % obj)

            out.openTag("record")

            out.openTag("datafield", [["tag", "970"], ["ind1", " "], ["ind2", " "]])
            out.writeTag("subfield", "INDICO.%s" % obj, [["code", "a"]])
            out.closeTag("datafield")

            out.openTag("datafield", [["tag", "980"], ["ind1", " "], ["ind2", " "]])
            out.writeTag("subfield", "DELETED", [["code", "c"]])
            out.closeTag("datafield")

            out.closeTag("record")

        elif isinstance(obj, conference.Conference):
            self.confToXMLMarc(obj, out=out, overrideCache=overrideCache)
        elif isinstance(obj, conference.Contribution):
            self.contToXMLMarc(obj, out=out, overrideCache=overrideCache)
        elif isinstance(obj, conference.SubContribution):
            self.subContToXMLMarc(obj, out=out, overrideCache=overrideCache)
        else:
            raise Exception("unknown object type: %s" % obj.__class__)
        return out.getXml()

    def confToXMLMarc(self, obj, out=None, overrideCache=False):
        if not out:
            out = self._XMLGen
        out.openTag("record")
        self._outGen.confToXMLMarc21(obj, out=out, overrideCache=overrideCache)
        out.closeTag("record")

    def sessionToXMLMarc(self, obj, out=None, overrideCache=False):
        if not out:
            out = self._XMLGen
        out.openTag("record")
        self._outGen.sessionToXMLMarc21(obj, out=out, overrideCache=overrideCache)
        out.closeTag("record")

    def contToXMLMarc(self, obj, out=None, overrideCache=False):
        if not out:
            out = self._XMLGen
        out.openTag("record")
        self._outGen.contribToXMLMarc21(obj, out=out, overrideCache=overrideCache)
        out.closeTag("record")

    def subContToXMLMarc(self, obj, out=None, overrideCache=False):
        if not out:
            out = self._XMLGen
        out.openTag("record")
        self._outGen.subContribToXMLMarc21(obj, out=out, overrideCache=overrideCache)
        out.closeTag("record")
