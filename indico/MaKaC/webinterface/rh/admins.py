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

from flask import session
from persistent.dict import PersistentDict
from werkzeug.exceptions import Forbidden

from indico.util.i18n import _

import MaKaC.webinterface.pages.admins as admins
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.common.info as info
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


class RHAdminArea(RHAdminBase):
    _uh = urlHandlers.UHAdminArea

    def _process(self):
        p = admins.WPAdmins(self)
        return p.display()


class RHUpdateNews( RHAdminBase ):
    _uh = urlHandlers.UHUpdateNews

    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        if self._params.has_key("news") and self._params.has_key("save"):
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            minfo.setNews(self._params["news"])
        p = admins.WPUpdateNews( self )
        return p.display()

class RHConfigUpcoming( RHAdminBase ):
    _uh = urlHandlers.UHConfigUpcomingEvents

    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        p = admins.WPConfigUpcomingEvents( self )
        return p.display()


class RHGeneralInfoModification(RHAdminBase):
    _uh = urlHandlers.UHGeneralInfoModification

    def _process(self):
        p = admins.WPGenInfoModification(self)
        return p.display()


class RHAdminSwitchNewsActive( RHAdminBase ):
    _uh = urlHandlers.UHAdminSwitchNewsActive

    def _process( self ):
        self._minfo.setNewsActive( not self._minfo.isNewsActive() )
        self._redirect( urlHandlers.UHAdminArea.getURL() )


class RHGeneralInfoPerformModification(RHAdminBase):
    _uh = urlHandlers.UHGeneralInfoPerformModification

    def _process(self):
        params = self._getRequestParams()

        if 'ok' in params:
            self._minfo.setTitle(params["title"])
            self._minfo.setOrganisation(params["organisation"])
            self._minfo.setCity(params["city"])
            self._minfo.setCountry(params["country"])
            self._minfo.setLang(params["lang"])
        self._redirect(urlHandlers.UHAdminArea.getURL())


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


class RHAdminLayoutSaveSocial(RHAdminBase):
    _uh = urlHandlers.UHAdminLayoutSaveSocial

    def _checkParams( self, params ):
        self._params = params
        RHAdminBase._checkParams( self, params )

    def _process(self):
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        cfg = minfo.getSocialAppConfig()
        if 'socialActive' in self._params:
            cfg['active'] = self._params.get('socialActive') == 'yes'
        if 'facebook_appId' in self._params:
            cfg.setdefault('facebook', PersistentDict())['appId'] = self._params.get('facebook_appId')
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
