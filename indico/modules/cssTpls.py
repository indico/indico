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

from persistent import Persistent
from MaKaC.common.Counter import Counter
from MaKaC.common.info import HelperMaKaCInfo
from indico.core.config import Config

from indico.modules import Module

class CssTplsModule(Module):
    """
    This module holds all the templates that can be used by a conference
    in order to display all the information.
    """
    id = "cssTpls"

    def __init__(self):
        self._cssTpls = {"template0.css": CSSItem("template0.css"), \
                         "right_menu.css": CSSItem("right_menu.css"),
                         "orange.css": CSSItem("orange.css"),
                         "brown.css": CSSItem("brown.css"),

                         "template_indico.css": CSSItem("template_indico.css")}
        self._p_changed = 1
        self._cssCounter = Counter()

    def getCssTplsList(self):
        return self._cssTpls.values()

    def getCssTplById(self, id):
        if self._cssTpls.has_key(id):
            return self._cssTpls[id]
        return None

    def addTemplate(self, tplId):
        """
        tplId must be the name of the css file
        """
        self._cssTpls[tplId] = CSSItem(tplId)

    def addLocalFile(self, lf):
        lf.setId(self._cssCounter.newCount())
        # TODO: add owner and repository
        self._cssTpls[lf.getId()] = CSSItem(lf)



class CSSItem(Persistent):
    """
    This class will handle a CSS template that can be applied
    to a conference display. CSS file can be an upload file or a
    template we already have. The upload file is an object of the class
    LocalFile and the template is just a string with the id (name) of the
    template.
    The class encapsulates the CSS so the user does not care about if it is
    a template or a local file.
    """

    def __init__(self, css):
        """
        A CSS item can be a local file or a template, but not both things at the same time.
        We keep to variables to make it readable, even if it would be possible to do the same
        thing with just one.

        _id is the same as _templateId when using a template and not a local file.
        """
        self._id = None
        self._localFile = None
        self._templateId = None
        if isinstance(css, str): # if css is not an object but a string, then we assume it is a template id.
            self._templateId = self._id = css
        else:
            self._localFile = css

    def getId(self):
        if self._localFile:
            return self._localFile.getId()
        else:
            return self._templateId

    def setId(self, i):
        self._id = i

    def isLocalFile(self):
        return self._localfile is not None

    def getLocalfile(self):
        return self._localFile

    def getLocator(self):
        loc = {}
        loc["cssId"] = self.getId()
        return loc

    def getURL(self):
        if self._localFile:
            # TODO: return a correct URL when possible to have files as templates
            #from MaKaC.webinterface.urlHandlers import UHConferenceCSS
            #return UHConferenceCSS.getURL(self._localFile)
            pass
        else:
            return "%s/%s"%(Config.getInstance().getCssConfTemplateBaseURL(),self._templateId)

    def getFileName(self, extension=True):
        if self._localFile:
            fn =self._localFile.getFileName()
        else:
            fn = self._templateId
        if not extension:
            fn = fn.lower().replace(".css","")
        return fn

    def getSize(self):
        if self._localFile:
            return self._localFile.getSize()
        else:
            # so size for direct templates
            return None

    def delete(self):
        if self._localFile:
            self._localFile.delete()
        self._localFile=None
        self._templateId=None
