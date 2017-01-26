# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from flask import session
from werkzeug.exceptions import Forbidden

from indico.util.i18n import _

import MaKaC.webinterface.pages.admins as admins
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common import HelperMaKaCInfo
from MaKaC.webinterface.rh.base import RHProtected


class RHAdminBase(RHProtected):
    def _checkParams(self, params):
        RHProtected._checkParams(self, params)
        self._minfo = HelperMaKaCInfo.getMaKaCInfoInstance()

    def _checkProtection(self):
        RHProtected._checkProtection(self)
        if not session.user and not self._doProcess:
            return
        if not session.user.is_admin:
            raise Forbidden(_("Only Indico administrators may access this page."))


class RHAdminLayoutGeneral(RHAdminBase):
    _uh = urlHandlers.UHAdminLayoutGeneral

    def _process(self):
        p = admins.WPAdminLayoutGeneral(self)
        return p.display()


class RHAdminLayoutSaveTemplateSet( RHAdminBase ):
    _uh = urlHandlers.UHAdminLayoutSaveTemplateSet

    def _checkParams( self, params ):
        self._params = params
        self._defSet = params.get("templateSet",None)
        if self._defSet == "None":
            self._defSet = None
        RHAdminBase._checkParams( self, params )

    def _process( self ):
        self._minfo.setDefaultTemplateSet(self._defSet)
        self._redirect( urlHandlers.UHAdminLayoutGeneral.getURL() )


class RHSystem(RHAdminBase):
    _uh = urlHandlers.UHAdminsSystem

    def _process( self ):

        p = admins.WPAdminsSystem( self )
        return p.display()

class RHSystemModify(RHAdminBase):

    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self._action = params.get("action", None)
        self._volume = params.get("volume", None)

    def _process( self ):
        if self._action == "ok":
            self._minfo.setArchivingVolume(self._volume)
            self._redirect(urlHandlers.UHAdminsSystem.getURL())
        elif self._action == "cancel":
            self._redirect(urlHandlers.UHAdminsSystem.getURL())
        else:
            p = admins.WPAdminsSystemModif( self )
            return p.display()

class RHConferenceStyles(RHAdminBase):
    _uh = urlHandlers.UHAdminsConferenceStyles

    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )

    def _process( self ):
        p = admins.WPAdminsConferenceStyles( self )
        return p.display()
