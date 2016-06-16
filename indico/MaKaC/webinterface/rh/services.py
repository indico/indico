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

from ipaddress import ip_address

import MaKaC.webinterface.rh.admins as admins
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common import utils
from MaKaC.common import info
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
            try:
                ipAddress = unicode(ip_address(ipAddress))
            except ValueError as exc:
                raise MaKaCError("IP Address {} is not valid: {}".format(ipAddress, exc))
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
