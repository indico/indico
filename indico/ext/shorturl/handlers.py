# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

# stdlib imports
import pkg_resources

# legacy imports
from MaKaC.services.implementation.base import ServiceBase
from MaKaC.plugins.base import PluginsHolder

# indico imports
from indico.web.rh import RHHtdocs
import indico.ext.shorturl


class RHShortUrlHtdocs(RHHtdocs):
    """
    Static file handler for Short URL plugin
    """

    _url = r"^/shorturl/(?P<filepath>.*)$"
    _local_path = pkg_resources.resource_filename(indico.ext.shorturl.__name__, "htdocs")
    _min_dir = 'shorturl'


class GetShortUrlGeneratorsService(ServiceBase):
    """
    Returns names and ids of active short url generators plugins.
    """
    def _getAnswer(self):
        generators = {}
        for plugin in PluginsHolder().getPluginType('shorturl').getPluginList():
            generators[plugin.getId()] = plugin.getName()
        return generators


methodMap = {
             "shorturl.getGenerators": GetShortUrlGeneratorsService,
             }
