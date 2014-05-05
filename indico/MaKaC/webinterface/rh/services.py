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

from flask import request

from indico.web.flask.util import url_for
import MaKaC.webinterface.rh.admins as admins
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common import utils
from MaKaC.common import info
from indico.core.config import Config
from MaKaC.webinterface.pages import admins as adminPages
from MaKaC.webinterface.rh import initial_setup
from MaKaC.errors import MaKaCError


class RHServicesBase(admins.RHAdminBase):
    pass


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


class RHInstanceTrackingBase(RHServicesBase):

    def _update(self):
        contact = request.form.get('contact', self._minfo.getInstanceTrackingContact())
        email = request.form.get('email', self._minfo.getInstanceTrackingEmail())
        uuid = self._minfo.getInstanceTrackingUUID()
        payload = {'enabled': True,
                   'url': Config.getInstance().getBaseURL(),
                   'contact': contact,
                   'email': email,
                   'organisation': self._minfo.getOrganisation()}
        initial_setup.update_instance(uuid, payload)

    def _register(self):
        contact = request.form.get('contact', self._minfo.getInstanceTrackingContact())
        email = request.form.get('email', self._minfo.getInstanceTrackingEmail())
        payload = {'url': Config.getInstance().getBaseURL(),
                   'contact': contact,
                   'email': email,
                   'organisation': self._minfo.getOrganisation()}
        initial_setup.register_instance(payload)


class RHInstanceTracking(RHInstanceTrackingBase):

    def _process_GET(self):
        p = adminPages.WPInstanceTracking(self)
        return p.display()

    def _process_POST(self):
        button_pressed = request.form['button-pressed']
        if button_pressed == 'save':
            enableNew = 'enable' in request.form
            enableOld = self._minfo.isInstanceTrackingActive()
            contact = request.form.get('contact', self._minfo.getInstanceTrackingContact())
            email = request.form.get('email', self._minfo.getInstanceTrackingEmail())
            self._minfo.setInstanceTrackingContact(contact)
            self._minfo.setInstanceTrackingEmail(email)
            uuid = self._minfo.getInstanceTrackingUUID()
            if enableNew and uuid == '':
                payload = {'url': Config.getInstance().getBaseURL(),
                           'contact': contact,
                           'email': email,
                           'organisation': self._minfo.getOrganisation()}
                initial_setup.register_instance(payload)
            elif enableNew and uuid != '':
                payload = {'enabled': True,
                           'contact': contact,
                           'email': email}
                initial_setup.update_instance(uuid, payload)
                self._minfo.setInstanceTrackingActive(True)
            elif enableOld and not enableNew:
                payload = {'enabled': False}
                initial_setup.update_instance(uuid, payload)
                self._minfo.setInstanceTrackingActive(False)
        elif button_pressed == 'update':
            requestType = request.form['update-it-type']
            if requestType == 'update':
                self._update()
            elif requestType == 'register':
                self._register()
        self._redirect(url_for("admin.adminServices-instanceTracking"))


class RHInstanceTrackingUpdate(RHInstanceTrackingBase):

    def _process(self):
        self._minfo.updateInstanceTrackingLastCheck()
        update = request.form['updateIT']
        if update == 'true':
            requestType = request.form['updateITType']
            if requestType == 'update':
                self._update()
            elif requestType == 'register':
                self._register()
