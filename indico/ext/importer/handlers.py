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

# stdlib imports
import pkg_resources

# legacy imports
from MaKaC.services.implementation.base import ServiceBase
from MaKaC.plugins.base import PluginsHolder

# indico imports
from indico.web.handlers import RHHtdocs
from indico.ext.importer.helpers import ImporterHelper
import indico.ext.importer


class RHImporterHtdocs(RHHtdocs):
    """Static file handler for Importer plugin"""

    _local_path = pkg_resources.resource_filename(indico.ext.importer.__name__, "htdocs")
    _min_dir = 'importer'


class DataImportService(ServiceBase):
    """
    Fetches data from the specified importer plugin.
    Arguments:
    query - string used in importer's search phrase
    importer - name of an importer plugin being used
    size - number of returned queries
    """

    def _checkParams(self):
        ServiceBase._checkParams(self)
        self._query = self._params['query']
        self._importer = self._params['importer']
        self._size = self._params.get('size', 10)

    def _getAnswer(self):
        importer = ImporterHelper.getImporter(self._importer)
        if importer:
            return importer.importData(self._query, self._size)

class GetImportersService(ServiceBase):
    """
    Returns names and ids of active importer plugins.
    """
    def _getAnswer(self):
        importers = {}
        for plugin in PluginsHolder().getPluginType('importer').getPluginList():
            importers[plugin.getId()] = plugin.getName()
        return importers


methodMap = {
             "importer.import" : DataImportService,
             "importer.getImporters": GetImportersService,
             }
