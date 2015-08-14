# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase
from MaKaC.webinterface import wcomponents, navigation
from MaKaC.errors import NotFoundError
from MaKaC.i18n import _


class WAuthorDisplay( wcomponents.WTemplated ):

    def __init__(self, aw, contrib, authId):
        self._aw = aw
        self._conf = contrib.getConference()
        self._contrib = contrib
        self._authorId = authId

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        authorObj = self._contrib.getAuthorById(self._authorId)

        not_found = NotFoundError(_("No author with id {} was found").format(self._authorId),
                                  title=_("Author not found"))

        if authorObj is None:
            raise not_found
        authorList = self._conf.getAuthorIndex().getByAuthorObj(authorObj)
        if authorList is None:
            raise not_found
        author = authorList[0]
        vars["contributions"] = [auth.getContribution()
                                 for auth in authorList if auth.getContribution().getConference()]
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
    menu_entry_name = 'author_index'

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
