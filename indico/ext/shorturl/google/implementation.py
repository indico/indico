# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.
import json
import requests
import indico.ext.shorturl.google

from indico.ext.shorturl.base.implementation import BaseShortUrlImplementation

from MaKaC.plugins.base import PluginsHolder
from MaKaC.webinterface.urlHandlers import UHConferenceDisplay


class GoogleShortUrlImplementation(BaseShortUrlImplementation):

    _name = 'Google'

    def __init__(self):
        BaseShortUrlImplementation.__init__(self)
        self._implementationPackage = indico.ext.shorturl.google

    @staticmethod
    def getVarFromPluginStorage(varName):
        """
        Retrieves varName from the options of the plugin.
        """
        piwik = PluginsHolder().getPluginType('shorturl').getPlugin('google')
        return piwik.getOptions()[varName].getValue()

    def generateShortURL(self, conf):
        """
        Returns a the short URL.
        """
        serviceURL = GoogleShortUrlImplementation.getVarFromPluginStorage("url")
        headers = {'content-type': 'application/json'}
        data = {'longUrl': str(UHConferenceDisplay.getURL(conf))}
        response = requests.post(serviceURL, data=json.dumps(data), headers=headers)
        return ("Google", response.json()["id"])

