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

from copy import copy

class RHPaymentModule:
    
    def __init__(self, req):
        self._req = req
    
    
    def process(self, params):
        from MaKaC import plugins
        epaymentModules = plugins.getPluginsByType("EPayment")
        module = None
        for mod in epaymentModules:
            params2 = copy(params)
##            mod.webinterface.rh.preprocessParams(params2)
##            if mod.pluginName == params2.get("EPaymentName","No module name"):
            if mod.webinterface.rh.preprocessParams(params2) and \
               mod.pluginName == params2.get("EPaymentName","No module name"):
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


