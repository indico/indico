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

import MaKaC.webinterface.rh.admins as admins
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common import utils
from MaKaC.common import info
import MaKaC.webcast as webcast
from MaKaC.errors import WebcastAdminError
from MaKaC.conference import ConferenceHolder
from MaKaC.webinterface.pages import admins as adminPages
from MaKaC.webinterface.rh.base import RHProtected
from MaKaC.errors import MaKaCError

class RHServicesBase(admins.RHAdminBase):
    pass

class RHWebcastBase( RHServicesBase ):

    def _checkProtection( self ):
        RHProtected._checkProtection( self )
        self._al = self._minfo.getAdminList()
        self._wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        if not self._wm.isManager( self._getUser() ) and not self._al.isAdmin( self._getUser() ):
            raise WebcastAdminError("management area")

class RHWebcast( RHWebcastBase ):
    _uh = urlHandlers.UHWebcast

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        p = adminPages.WPWebcast(self)
        return p.display()

class RHWebcastArchive( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastArchive

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        p = adminPages.WPWebcastArchive(self)
        return p.display()

class RHWebcastSetup( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastSetup

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        p = adminPages.WPWebcastSetup(self)
        return p.display()


class RHWebcastAddWebcast( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastAddWebcast

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._eventid = params.get("eventid","")
        self._params = params

    def _process( self ):
        event = ConferenceHolder().getById(self._eventid)
        if event:
            self._wm.addForthcomingWebcast(event)
        self._redirect(urlHandlers.UHWebcast.getURL())

class RHWebcastRemoveWebcast( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastRemoveWebcast

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._webcastid = params.get("webcastid","")
        self._params = params

    def _process( self ):
        if self._webcastid != "":
            if self._wm.deleteForthcomingWebcastById(self._webcastid):
                self._redirect(urlHandlers.UHWebcast.getURL())
            elif self._wm.deleteArchivedWebcastById(self._webcastid):
                self._redirect(urlHandlers.UHWebcastArchive.getURL())
            else:
                self._redirect(urlHandlers.UHWebcast.getURL())
        else:
            self._redirect(urlHandlers.UHWebcast.getURL())

class RHWebcastArchiveWebcast( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastArchiveWebcast

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._webcastid = params.get("webcastid","")
        self._params = params

    def _process( self ):
        if self._webcastid != "":
            self._wm.archiveForthcomingWebcastById(self._webcastid)
        self._redirect(urlHandlers.UHWebcast.getURL())

class RHWebcastUnArchiveWebcast( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastUnArchiveWebcast

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._webcastid = params.get("webcastid","")
        self._params = params

    def _process( self ):
        if self._webcastid != "":
            self._wm.unArchiveWebcastById(self._webcastid)
        self._redirect(urlHandlers.UHWebcastArchive.getURL())

class RHWebcastAddChannel( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastAddChannel

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._action = ""
        if params.get("submit","") == "add channel":
            self._action = "addchannel"
            self._chname = params.get("chname","")
            self._churl = params.get("churl","")
            self._chwidth = params.get("chwidth",480)
            self._chheight = params.get("chheight",360)
        self._params = params

    def _process( self ):
        if self._action == "addchannel":
            if self._wm.getChannel(self._chname):
                self._wm.getChannel(self._chname).setValues(self._chname, self._churl, self._chwidth, self._chheight)
            else:
                self._wm.addChannel(self._chname, self._churl, self._chwidth, self._chheight)
        self._redirect(urlHandlers.UHWebcastSetup.getURL())

class RHWebcastModifyChannel( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastModifyChannel

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._action = ""
        if params.get("submit","") == "modify channel":
            self._action = "modifychannel"
            self._choldname = params.get("chname","")
            self._chnewname = params.get("chnewname","")
            self._churl = params.get("churl","")
            self._chwidth = params.get("chwidth",480)
            self._chheight = params.get("chheight",360)
        self._params = params

    def _process( self ):
        if self._action == "modifychannel":
            if self._wm.getChannel(self._choldname):
                self._wm.getChannel(self._choldname).setValues(self._chnewname, self._churl, self._chwidth, self._chheight)
        self._redirect(urlHandlers.UHWebcastSetup.getURL())

class RHWebcastRemoveChannel( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastRemoveChannel

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._chname = params.get("chname","")
        self._params = params

    def _process( self ):
        if self._chname != "":
            self._wm.removeChannel(self._chname)
        self._redirect(urlHandlers.UHWebcastSetup.getURL())

class RHWebcastSwitchChannel( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastSwitchChannel

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._chname = params.get("chname","")
        self._params = params

    def _process( self ):
        if self._chname != "":
            self._wm.switchChannel(self._chname)
        self._redirect(urlHandlers.UHWebcast.getURL())

class RHWebcastMoveChannelUp( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastMoveChannelUp

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._chnb = params.get("chnb","")
        self._params = params

    def _process( self ):
        if self._chnb != "":
            self._wm.moveChannelUp(int(self._chnb))
        self._redirect(urlHandlers.UHWebcastSetup.getURL())

class RHWebcastMoveChannelDown( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastMoveChannelDown

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._chnb = params.get("chnb","")
        self._params = params

    def _process( self ):
        if self._chnb != "":
            self._wm.moveChannelDown(int(self._chnb))
        self._redirect(urlHandlers.UHWebcastSetup.getURL())

class RHWebcastSaveWebcastSynchronizationURL( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastSetup

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._webcastSynchronizationURL = params.get('webcastSynchronizationURL', '')
        self._params = params

    def _process( self ):
        self._wm.setWebcastSynchronizationURL(self._webcastSynchronizationURL)
        self._redirect(urlHandlers.UHWebcastSetup.getURL())


class RHWebcastManuelSynchronizationURL( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastSetup

    def _process( self ):
        answer = self._wm.remoteSynchronize(raiseExceptionOnSyncFail = True)
        if answer:
            return "Answer obtained by Indico:" + answer
        else:
            self._redirect(urlHandlers.UHWebcastSetup.getURL())


class RHWebcastAddStream( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastAddStream

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._action = ""
        if params.get("submit","") == "add stream":
            self._action = "addstream"
            self._chname = params.get("chname","")
            self._format = params.get("stformat","")
            self._url = params.get("sturl","")
        self._params = params

    def _process( self ):
        if self._action == "addstream":
            ch = self._wm.getChannel(self._chname)
            if ch:
                ch.addStream(self._format, self._url)
        self._redirect(urlHandlers.UHWebcastSetup.getURL())

class RHWebcastRemoveStream( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastRemoveStream

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._chname = params.get("chname","")
        self._format = params.get("stformat","")
        self._params = params

    def _process( self ):
        ch = self._wm.getChannel(self._chname)
        if ch:
            ch.removeStream(self._format)
        self._redirect(urlHandlers.UHWebcastSetup.getURL())

class RHWebcastAddOnAir( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastAddOnAir

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._action = ""
        self._chname = params.get("chname","")
        self._eventid = params.get("eventid","")
        self._params = params

    def _process( self ):
        wc = self._wm.getForthcomingWebcastById(self._eventid)
        if wc:
            self._wm.setOnAir(self._chname, wc)
        self._redirect(urlHandlers.UHWebcast.getURL())

class RHWebcastRemoveFromAir( RHWebcastBase ):
    _uh = urlHandlers.UHWebcastRemoveFromAir

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._chname = params.get("chname","")
        self._params = params

    def _process( self ):
        if self._chname != "":
            self._wm.removeFromAir(self._chname)
        self._redirect(urlHandlers.UHWebcast.getURL())

class RHIPBasedACL( RHServicesBase ):
    """ IP Based ACL Configuration Interface """

    _uh = urlHandlers.UHIPBasedACL

    def _process( self ):
        p = adminPages.WPIPBasedACL(self)
        return p.display()

class RHIPBasedACLFullAccessGrant( RHServicesBase ):

    _uh = urlHandlers.UHIPBasedACLFullAccessGrant

    def _checkParams( self, params ):
        RHServicesBase._checkParams( self, params )
        self._params = params

    def _process( self ):

        ipAddress = self._params.get('ipAddress', None)

        if ipAddress:
            if not utils.validIP(ipAddress):
                raise MaKaCError("IP Address %s is  not valid!" % ipAddress)
            else:
                minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
                ip_acl_mgr = minfo.getIPBasedACLMgr()
                ip_acl_mgr.grant_full_access(ipAddress)

        self._redirect(urlHandlers.UHIPBasedACL.getURL())

class RHIPBasedACLFullAccessRevoke( RHServicesBase ):

    _uh = urlHandlers.UHIPBasedACLFullAccessRevoke

    def _checkParams( self, params ):
        RHServicesBase._checkParams( self, params )
        self._params = params

    def _process( self ):

        ipAddress = self._params.get('ipAddress', None)

        if ipAddress:
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            ip_acl_mgr = minfo.getIPBasedACLMgr()
            ip_acl_mgr.revoke_full_access(ipAddress)

        self._redirect(urlHandlers.UHIPBasedACL.getURL())

class RHAnalytics( RHServicesBase ):
    _uh = urlHandlers.UHAnalytics

    def _process( self ):
        p = adminPages.WPAnalytics(self)
        return p.display()


class RHSaveAnalytics(RHServicesBase):
    _uh = urlHandlers.UHSaveAnalytics

    def _checkParams( self, params ):
        RHServicesBase._checkParams( self, params )
        self._params = params
        self._analyticsActive = self._params.get('analyticsActive') == 'yes'
        self._analyticsCode = self._params.get('analyticsCode')
        self._analyticsCodeLocation = self._params.get('analyticsCodeLocation')
        self._doNotSanitizeFields.append("analyticsCode")

    def _process(self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if 'analyticsActive' in self._params:
            minfo.setAnalyticsActive(self._analyticsActive)
        if 'analyticsCode' in self._params:
            minfo.setAnalyticsCode(self._analyticsCode)
        if 'analyticsCodeLocation' in self._params:
            minfo.setAnalyticsCodeLocation(self._analyticsCodeLocation)
        self._redirect( urlHandlers.UHAnalytics.getURL() )
