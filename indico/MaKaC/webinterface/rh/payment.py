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

from copy import copy
from MaKaC.plugins import pluginId

class RHPaymentModule:

    def __init__(self, req):
        self._req = req


    def process(self, params):
        from MaKaC.plugins import PluginLoader
        epaymentModules = PluginLoader.getPluginsByType("EPayment")
        module = None
        for mod in epaymentModules:
            params2 = copy(params)
            if mod.webinterface.rh.preprocessParams(params2) and \
                   mod.MODULE_ID == params2.get("EPaymentName","No module name"):
                module = mod
                break
        if module:
            rhmod = module.webinterface.rh
            rhmod.preprocessParams(params)
            requestTag = params.get("requestTag", "No requestTag")
            rh = rhmod.getRHByTag(rhmod, requestTag)
            if rh:
                return rh(self._req).process(params)
        return ""


