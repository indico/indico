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

"""
Contains definitions for the plugin's web interface
"""

# system lib imports
import pkg_resources

# 3rd party lib imports
import zope.interface

# indico extpoint imports
from indico.core.extpoint import Component
from indico.core.extpoint.plugins import IPluginSettingsContributor
from indico.web.handlers import RHHtdocs

# legacy indico imports
from MaKaC.webinterface.urlHandlers import URLHandler
from MaKaC.webinterface.wcomponents import WTemplated
import MaKaC.plugins.EPayment
from MaKaC.plugins import PluginsHolder


class UHEPaymentHtdocs(URLHandler):
    """URL handler for epayment status"""
    _endpoint = 'epayment.htdocs'

# Request Handlers


class RHEPaymentHtdocs(RHHtdocs):
    """Static file handler for EPayment plugin"""
    _local_path = pkg_resources.resource_filename(MaKaC.plugins.EPayment.__name__, "htdocs")


# Plugin Settings

class PluginSettingsContributor(Component):
    """
    Plugs to the IPluginSettingsContributor extension point, providing a "plugin
    settings" web interface
    """

    zope.interface.implements(IPluginSettingsContributor)

    def hasPluginSettings(self, obj, ptype, plugin):
        if ptype == 'EPayment' and plugin == None:
            return True
        else:
            return False

    def getPluginSettingsHTML(self, obj, ptype, plugin):
        if ptype == 'EPayment' and plugin == None:
            return WPluginSettings.forModule(MaKaC.plugins.EPayment).getHTML()
        else:
            return None


class WPluginSettings(WTemplated):

    def getVars(self):
        ph = PluginsHolder()

        tplVars = WTemplated.getVars(self)
        tplVars["epayment_htdocs"] = UHEPaymentHtdocs
        tplVars["currency_data"] = ph.getPluginType('EPayment').getOption("customCurrency").getValue()
        return tplVars


