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

import requests
from flask import request
from json import dumps

from indico.web.flask.util import url_for
import MaKaC.webinterface.rh.admins as admins
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common import utils
from MaKaC.common import info
from indico.core.config import Config
from MaKaC.webinterface.pages import admins as adminPages
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


def register_instance(contact, email):
    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
    payload = {'url': Config.getInstance().getBaseURL(),
               'contact': contact,
               'email': email,
               'organisation': minfo.getOrganisation()}
    url = Config.getInstance().getTrackerURL() + '/instance/'
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=dumps(payload), headers=headers).json()
        uuid = response['uuid']
    except (requests.exceptions.RequestException, ValueError, KeyError):
        minfo.setInstanceTrackingActive(False)
        return False
    else:
        minfo.setInstanceTrackingActive(True)
        minfo.setInstanceTrackingUUID(uuid)
        minfo.setInstanceTrackingContact(payload['contact'])
        minfo.setInstanceTrackingEmail(payload['email'])
    return True


def update_instance(contact, email):
    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
    uuid = minfo.getInstanceTrackingUUID()
    payload = {'enabled': True,
               'url': Config.getInstance().getBaseURL(),
               'contact': contact,
               'email': email,
               'organisation': minfo.getOrganisation()}
    url = "{0}/instance/{1}".format(Config.getInstance().getTrackerURL(), uuid)
    headers = {'Content-Type': 'application/json'}
    response = requests.patch(url, data=dumps(payload), headers=headers)
    if response.status_code >= 400:
        register_instance(contact, email)
    else:
        minfo.setInstanceTrackingActive(True)
        minfo.setInstanceTrackingContact(payload['contact'])
        minfo.setInstanceTrackingEmail(payload['email'])
    return True


def disable_instance():
    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

    uuid = minfo.getInstanceTrackingUUID()
    payload = {'enabled': False}
    url = "{0}/instance/{1}".format(Config.getInstance().getTrackerURL(), uuid)
    headers = {'Content-Type': 'application/json'}
    response = requests.patch(url, data=dumps(payload), headers=headers)
    if response.status_code >= 400 and response.status_code != 404:
        return False
    else:
        minfo.setInstanceTrackingActive(False)
    return True


def sync_instance(request_type):
    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
    contact = request.form.get('contact', minfo.getInstanceTrackingContact())
    email = request.form.get('email', minfo.getInstanceTrackingEmail())
    if request_type == 'register':
        register_instance(contact, email)
    update_instance(contact, email)


class RHInstanceTracking(RHServicesBase):

    def _process_GET(self):
        p = adminPages.WPInstanceTracking(self)
        return p.display()

    def _process_POST(self):
        button_pressed = request.form['button_pressed']
        contact = request.form.get('contact', self._minfo.getInstanceTrackingContact())
        email = request.form.get('email', self._minfo.getInstanceTrackingEmail())
        if button_pressed == 'save':
            enableNew = 'enable' in request.form
            enableOld = self._minfo.isInstanceTrackingActive()
            uuid = self._minfo.getInstanceTrackingUUID()
            # If enabled and without uuid --> register
            if enableNew and uuid == '':
                register_instance(contact, email)
            # If enabled with an uuid --> register/update everything
            elif enableNew and uuid != '':
                sync_instance(request.form['update_it_type'])
            # If set to disabled --> update only activation
            elif enableOld and not enableNew:
                disable_instance()
            # Else if disabled and something else changed --> update nothing
        elif button_pressed == 'sync':
            sync_instance(request.form['update_it_type'])
        elif button_pressed == 'cancel':
            disable_instance()
        self._redirect(url_for("admin.adminServices-instanceTracking"))
