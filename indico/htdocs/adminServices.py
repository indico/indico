# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import MaKaC.webinterface.rh.services as services

def webcast(req, **params):
    return services.RHWebcast(req).process(params)

def webcastICal(req, **params):
    return services.RHWebcastICal(req).process(params)

def webcastArchive(req, **params):
    return services.RHWebcastArchive(req).process(params)

def webcastSetup(req, **params):
    return services.RHWebcastSetup(req).process(params)

def webcastSelectManager(req, **params):
    return services.RHWebcastSelectManager(req).process(params)

def webcastAddManager(req, **params):
    return services.RHWebcastAddManager(req).process(params)

def webcastRemoveManager(req, **params):
    return services.RHWebcastRemoveManager(req).process(params)

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

def webcastSaveWebcastServiceURL(req, **params):
    return services.RHWebcastSaveWebcastServiceURL(req).process(params)

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

def recording(req, **params):
    return services.RHRecording(req).process(params)

def oaiPrivateConfig(req, **params):
    return services.RHOAIPrivateConfig(req).process(params)

def oaiPrivateConfigAddIP(req, **params):
    return services.RHOAIPrivateConfigAddIP(req).process(params)

def oaiPrivateConfigRemoveIP(req, **params):
    return services.RHOAIPrivateConfigRemoveIP(req).process(params)
