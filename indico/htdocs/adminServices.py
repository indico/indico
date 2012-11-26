# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

import MaKaC.webinterface.rh.services as services
import MaKaC.webinterface.rh.api as api

def webcast(req, **params):
    return services.RHWebcast(req).process(params)

def webcastArchive(req, **params):
    return services.RHWebcastArchive(req).process(params)

def webcastSetup(req, **params):
    return services.RHWebcastSetup(req).process(params)

def webcastAddWebcast(req, **params):
    return services.RHWebcastAddWebcast(req).process(params)

def webcastRemoveWebcast(req, **params):
    return services.RHWebcastRemoveWebcast(req).process(params)

def webcastArchiveWebcast(req, **params):
    return services.RHWebcastArchiveWebcast(req).process(params)

def webcastUnArchiveWebcast(req, **params):
    return services.RHWebcastUnArchiveWebcast(req).process(params)

def webcastAddChannel(req, **params):
    return services.RHWebcastAddChannel(req).process(params)

def webcastModifyChannel(req, **params):
    return services.RHWebcastModifyChannel(req).process(params)

def webcastRemoveChannel(req, **params):
    return services.RHWebcastRemoveChannel(req).process(params)

def webcastSwitchChannel(req, **params):
    return services.RHWebcastSwitchChannel(req).process(params)

def webcastMoveChannelUp(req, **params):
    return services.RHWebcastMoveChannelUp(req).process(params)

def webcastMoveChannelDown(req, **params):
    return services.RHWebcastMoveChannelDown(req).process(params)

def webcastSaveWebcastSynchronizationURL(req, **params):
    return services.RHWebcastSaveWebcastSynchronizationURL(req).process(params)

def webcastManualSynchronization(req, **params):
    return services.RHWebcastManuelSynchronizationURL(req).process(params)

def webcastAddStream(req, **params):
    return services.RHWebcastAddStream(req).process(params)

def webcastRemoveStream(req, **params):
    return services.RHWebcastRemoveStream(req).process(params)

def webcastAddOnAir(req, **params):
    return services.RHWebcastAddOnAir(req).process(params)

def webcastRemoveFromAir(req, **params):
    return services.RHWebcastRemoveFromAir(req).process(params)

def ipbasedacl(req, **params):
    return services.RHIPBasedACL(req).process(params)

def ipbasedacl_fagrant(req, **params):
    return services.RHIPBasedACLFullAccessGrant(req).process(params)

def ipbasedacl_farevoke(req, **params):
    return services.RHIPBasedACLFullAccessRevoke(req).process(params)

def apiOptions(req, **params):
    return api.RHAdminAPIOptions(req).process(params)

def apiOptionsSet(req, **params):
    return api.RHAdminAPIOptionsSet(req).process(params)

def apiKeys(req, **params):
    return api.RHAdminAPIKeys(req).process(params)

def analytics(req, **params):
    return services.RHAnalytics(req).process(params)

def saveAnalytics(req, **params):
    return services.RHSaveAnalytics(req).process(params)
