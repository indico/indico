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
from flask import request

from xml.sax.saxutils import quoteattr

from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase
from MaKaC.webinterface import wcomponents, navigation, urlHandlers
from MaKaC.errors import MaKaCError
from indico.core.config import Config
from MaKaC.common.fossilize import fossilize
from MaKaC.i18n import _
from MaKaC.conference import Link


class WAuthorDisplay( wcomponents.WTemplated ):

    def __init__(self, aw, contrib, authId):
        self._aw = aw
        self._conf = contrib.getConference()
        self._contrib = contrib
        self._authorId = authId

    def _getMaterial(self, contrib):
        materials = []
        for material in contrib.getAllMaterialList():
            resources = []
            for resource in material.getResourceList():
                resources.append({
                        'name': resource.getName(),
                        'url': str(urlHandlers.UHMaterialDisplay.getURL(resource)) if isinstance(resource, Link) \
                            else str(urlHandlers.UHFileAccess.getURL(resource))})
            materials.append({'title': material.getTitle(), 'resources': resources})
        return materials

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        authorObj = self._contrib.getAuthorById(self._authorId)
        if authorObj is None:
            raise MaKaCError(_("Not found the author: %s") % self._authorId)
        authorList = self._conf.getAuthorIndex().getByAuthorObj(authorObj)
        author = None
        if authorList is not None:
            author = authorList[0]
        else:
            raise MaKaCError(_("Not found the author: %s") % self._authorId)
        contribList = []
        for auth in authorList:
            contrib = auth.getContribution()
            if contrib is not None:
                contribList.append({'title': contrib.getTitle(),
                                    'url': str(urlHandlers.UHContributionDisplay.getURL(auth.getContribution())),
                                    'materials': fossilize(contrib.getAllMaterialList())})
        vars["contributions"] = contribList
        vars["fullName"] = author.getFullName()
        if self._aw.getUser() is not None:
            vars["email"] = author.getEmail()
        vars["address"] = author.getAddress()
        vars["telephone"] = author.getPhone()
        vars["fax"] = author.getFax()
        vars["affiliation"] = author.getAffiliation()
        return vars


class WPAuthorDisplay(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEAuthorDisplay

    def __init__(self, rh, contrib, authId):
        WPConferenceDefaultDisplayBase.__init__(self, rh, contrib.getConference())
        self._authorId = authId
        self._contrib = contrib

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
            self._asset_env['indico_authors'].urls()

    def _getBody(self, params):
        wc = WAuthorDisplay(self._getAW(), self._contrib, self._authorId)
        return wc.getHTML()

    def _defineSectionMenu(self):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._authorIndexOpt)
