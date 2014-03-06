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

from flask import session
from persistent.dict import PersistentDict

import MaKaC.webinterface.pages.admins as admins
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.common.info as info
from MaKaC.errors import AdminError
from MaKaC.common import HelperMaKaCInfo
from MaKaC.webinterface.rh.base import RHProtected

from indico.web.flask.util import url_for


class RHAdminBase(RHProtected):
    def _checkParams(self, params):
        RHProtected._checkParams(self, params)
        self._minfo = HelperMaKaCInfo.getMaKaCInfoInstance()

    def _checkProtection(self):
        RHProtected._checkProtection(self)
        if not session.user and not self._doProcess:
            return
        if not session.user.is_admin:
            raise AdminError("area")


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


class RHAdminToggleInstanceTracking(RHAdminBase):

    def _process(self):
        self._minfo.setInstanceTrackingActive(not self._minfo.isInstanceTrackingActive())
        self._redirect(url_for('admin.adminList'))


class RHGeneralInfoPerformModification(RHAdminBase):
    _uh = urlHandlers.UHGeneralInfoPerformModification

    def _process(self):
        params = self._getRequestParams()

        if params['action'] != 'cancel':
            self._minfo.setTitle(params["title"])
            self._minfo.setOrganisation(params["organisation"])
            self._minfo.setCity(params["city"])
            self._minfo.setCountry(params["country"])
            self._minfo.setTimezone(params["timezone"])
            self._minfo.setLang(params["lang"])
        self._redirect(urlHandlers.UHAdminArea.getURL())


class RHStyles(RHAdminBase):
    _uh = urlHandlers.UHAdminsStyles

    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self._new = params.get("new", "")
        self._name = params.get("name", "")
        self._styleID = params.get("styleID", "")
        self._tplfile = params.get("tplfile", "")
        self._useCss = params.get("useCss", "")
        self._cssfile = params.get("cssfile", "")
        self._eventType = params.get("event_type", "")
        self._action = params.get("action", "")
        self._newstyle = params.get("newstyle","")
        self._stylesheetfile = params.get("stylesheetfile", "")
        self._typeTemplate = params.get("templatetype", "")


    def _process( self ):
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        if self._new != "":
            if self._styleID not in styleMgr.getStyles().keys() and self._name != "" and self._styleID != "":
                styles = styleMgr.getStyles()
                if not self._useCss:
                    self._cssfile = None
                if self._typeTemplate == 'xsl':
                    file = self._stylesheetfile
                else:
                    file = self._tplfile
                styles[self._styleID] = (self._name, file, self._cssfile)
                styleMgr.setStyles(styles)
        if self._action == "default" and self._eventType != "" and self._tplfile != "":
            styleMgr.setDefaultStyle(self._tplfile, self._eventType)
        if self._action == "delete" and self._eventType != "" and self._tplfile != "":
            styleMgr.removeStyle(self._tplfile, self._eventType)
        if self._action == "add" and self._eventType != "" and self._newstyle != "":
            styleMgr.addStyleToEventType(self._newstyle, self._eventType)
        p = admins.WPAdminsStyles( self )
        return p.display()

class RHDeleteStyle(RHAdminBase):
    _uh = urlHandlers.UHAdminsDeleteStyle

    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self._tplfile = params.get("templatefile", "")
        self._eventType = params.get("event_type","")

    def _process( self ):
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        if self._tplfile != "":
            styleMgr.removeStyle(self._tplfile, self._eventType)
        self._redirect(urlHandlers.UHAdminsStyles.getURL())

class RHAddStyle(RHAdminBase):
    _uh = urlHandlers.UHAdminsAddStyle

    def _process( self ):
        p = admins.WPAdminsAddStyle( self )
        return p.display()


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

class RHAdminProtection( RHAdminBase ):
    _uh = urlHandlers.UHDomains

    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )

    def _process( self ):
        p = admins.WPAdminProtection( self )
        return p.display()
